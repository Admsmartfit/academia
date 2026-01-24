# app/routes/shop.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app.models import Package, Subscription, Payment, PaymentStatusEnum, SubscriptionStatus, PaymentStatus, Modality
from app import db
from datetime import datetime, timedelta

shop_bp = Blueprint('shop', __name__, url_prefix='/shop')


@shop_bp.route('/')
def packages():
    """Loja de pacotes - estilo e-commerce"""
    packages = Package.query.filter_by(is_active=True).order_by(
        Package.display_order,
        Package.id
    ).all()
    
    modalities = Modality.query.filter_by(is_active=True).order_by(Modality.name).all()

    import json
    packages_json = json.dumps([{
        'id': p.id,
        'name': p.name,
        'credits': p.credits,
        'price': float(p.price)
    } for p in packages])

    return render_template('shop/packages.html', packages=packages, modalities=modalities, packages_json=packages_json)


@shop_bp.route('/package/<int:id>')
def package_detail(id):
    """Detalhes de um pacote especifico"""
    package = Package.query.get_or_404(id)

    if not package.is_active:
        flash('Este pacote nao esta mais disponivel.', 'warning')
        return redirect(url_for('shop.packages'))

    return render_template('shop/package_detail.html', package=package)


@shop_bp.route('/checkout/<int:package_id>', methods=['GET', 'POST'])
@login_required
def checkout(package_id):
    """Finalizar compra"""
    package = Package.query.get_or_404(package_id)

    if not package.is_active:
        flash('Este pacote nao esta disponivel.', 'warning')
        return redirect(url_for('shop.packages'))

    if request.method == 'POST':
        payment_method = request.form.get('payment_method', 'pix_manual')

        # Criar assinatura
        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=package.validity_days)

        subscription = Subscription(
            user_id=current_user.id,
            package_id=package.id,
            credits_total=package.credits,
            credits_used=0,
            start_date=start_date,
            end_date=end_date,
            status=SubscriptionStatus.ACTIVE,
            payment_status=PaymentStatus.PENDING
        )

        db.session.add(subscription)
        db.session.flush()  # Para obter o ID

        # Criar parcelas de pagamento
        installment_value = package.installment_price
        first_payment = None

        for i in range(1, package.installments + 1):
            # Vencimento: primeiro pagamento hoje, proximos a cada 30 dias
            if i == 1:
                due_date = start_date
            else:
                due_date = start_date + timedelta(days=30 * (i - 1))

            payment = Payment(
                subscription_id=subscription.id,
                installment_number=i,
                installment_total=package.installments,
                amount=installment_value,
                due_date=due_date,
                status=PaymentStatusEnum.PENDING,
                payment_method=payment_method
            )

            db.session.add(payment)

            if i == 1:
                first_payment = payment

        db.session.commit()

        # Se escolheu NuPay PIX, gerar o PIX automaticamente
        if payment_method == 'nupay_pix' and current_user.cpf:
            try:
                from app.services.nupay import NuPayService, NuPayError

                nupay = NuPayService()
                result = nupay.create_pix_payment(first_payment, current_user)

                # Salvar dados do PIX no payment
                first_payment.nupay_reference_id = f"PAYMENT_{first_payment.id}"
                first_payment.nupay_psp_reference_id = result.get('pspReferenceId')
                first_payment.nupay_payment_url = result.get('paymentUrl')
                first_payment.nupay_qr_code = result.get('qrCode', {}).get('data')
                first_payment.nupay_pix_copy_paste = result.get('pixCopyPaste')

                db.session.commit()

                return render_template(
                    'shop/pix_payment.html',
                    payment=first_payment,
                    pix_data=result
                )

            except NuPayError as e:
                flash(f'Erro ao gerar PIX: {str(e)}. Tente novamente ou use o PIX manual.', 'danger')
                return redirect(url_for('student.my_subscriptions'))

            except Exception as e:
                flash('Erro ao processar pagamento. Tente novamente.', 'danger')
                return redirect(url_for('student.my_subscriptions'))

        # PIX manual - redirecionar para minhas assinaturas
        flash(f'Pacote "{package.name}" adquirido! Faca o pagamento da primeira parcela.', 'success')
        return redirect(url_for('student.my_subscriptions'))

    return render_template('shop/checkout.html', package=package)


@shop_bp.route('/payment/<int:payment_id>/upload', methods=['POST'])
@login_required
def upload_payment_proof(payment_id):
    """Upload de comprovante de pagamento"""
    payment = Payment.query.get_or_404(payment_id)

    # Verificar se e do usuario logado
    if payment.subscription.user_id != current_user.id:
        abort(403)

    if 'proof' not in request.files:
        flash('Nenhum arquivo selecionado.', 'danger')
        return redirect(url_for('student.my_subscriptions'))

    file = request.files['proof']

    if file.filename == '':
        flash('Nenhum arquivo selecionado.', 'danger')
        return redirect(url_for('student.my_subscriptions'))

    # Salvar arquivo
    try:
        from app.services.image_handler import save_payment_proof
        proof_url = save_payment_proof(file, current_user.id, payment.id)

        payment.proof_url = proof_url
        db.session.commit()

        flash('Comprovante enviado! Aguarde aprovacao da academia.', 'success')
    except ValueError as e:
        flash(str(e), 'danger')

    return redirect(url_for('student.my_subscriptions'))


@shop_bp.route('/generate-pix/<int:payment_id>', methods=['POST'])
@login_required
def generate_pix(payment_id):
    """Gera PIX via NuPay para um pagamento"""
    payment = Payment.query.get_or_404(payment_id)

    # Verificar se é do usuário logado
    if payment.subscription.user_id != current_user.id:
        abort(403)

    # Verificar se já não foi pago
    if payment.status == PaymentStatusEnum.PAID:
        flash('Este pagamento já foi confirmado.', 'info')
        return redirect(url_for('student.my_subscriptions'))

    # Verificar se usuário tem CPF cadastrado
    if not current_user.cpf:
        flash('É necessário cadastrar seu CPF para pagamento via PIX.', 'warning')
        return redirect(url_for('student.profile_edit'))

    try:
        from app.services.nupay import NuPayService, NuPayError

        nupay = NuPayService()
        result = nupay.create_pix_payment(payment, current_user)

        # Salvar dados do PIX no payment
        payment.nupay_reference_id = f"PAYMENT_{payment.id}"
        payment.nupay_psp_reference_id = result.get('pspReferenceId')
        payment.nupay_payment_url = result.get('paymentUrl')
        payment.nupay_qr_code = result.get('qrCode', {}).get('data')
        payment.nupay_pix_copy_paste = result.get('pixCopyPaste')
        payment.payment_method = 'nupay_pix'

        db.session.commit()

        return render_template(
            'shop/pix_payment.html',
            payment=payment,
            pix_data=result
        )

    except NuPayError as e:
        flash(f'Erro ao gerar PIX: {str(e)}', 'danger')
        return redirect(url_for('student.my_subscriptions'))

    except Exception as e:
        flash('Erro ao processar pagamento. Tente novamente.', 'danger')
        return redirect(url_for('student.my_subscriptions'))


@shop_bp.route('/payment-status/<int:payment_id>')
@login_required
def payment_status(payment_id):
    """Verifica status do pagamento (para polling AJAX)"""
    payment = Payment.query.get_or_404(payment_id)

    # Verificar se é do usuário logado
    if payment.subscription.user_id != current_user.id:
        return {'error': 'Forbidden'}, 403

    # Se tem PSP reference, consultar NuPay
    if payment.nupay_psp_reference_id and payment.status != PaymentStatusEnum.PAID:
        try:
            from app.services.nupay import NuPayService

            nupay = NuPayService()
            result = nupay.get_payment_status(payment.nupay_psp_reference_id)

            nupay_status = result.get('status', '')

            # Atualizar se mudou para COMPLETED
            if nupay_status == 'COMPLETED' and payment.status != PaymentStatusEnum.PAID:
                payment.mark_as_paid()
                db.session.commit()

        except Exception:
            pass  # Ignorar erros de consulta

    return {
        'payment_id': payment.id,
        'status': payment.status.value,
        'is_paid': payment.status == PaymentStatusEnum.PAID,
        'paid_date': payment.paid_date.isoformat() if payment.paid_date else None
    }


@shop_bp.route('/checkout/success')
@login_required
def checkout_success():
    """Página de sucesso após pagamento"""
    # Buscar última subscription do usuário
    subscription = Subscription.query.filter_by(
        user_id=current_user.id
    ).order_by(Subscription.created_at.desc()).first()

    return render_template('shop/success.html', subscription=subscription)


@shop_bp.route('/checkout/cancel')
@login_required
def checkout_cancel():
    """Página quando usuário cancela pagamento"""
    flash('Pagamento cancelado. Você pode tentar novamente quando quiser.', 'info')
    return redirect(url_for('student.my_subscriptions'))
