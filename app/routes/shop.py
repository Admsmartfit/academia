# app/routes/shop.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app.models import Package, Subscription, Payment, PaymentStatusEnum, SubscriptionStatus, PaymentStatus, Modality
from app import db
from datetime import datetime, timedelta
from decimal import Decimal

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
                status=PaymentStatusEnum.PENDING
            )

            db.session.add(payment)

        db.session.commit()

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
