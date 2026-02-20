# app/routes/admin/payments.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required
from app.models import Payment, PaymentStatusEnum, Subscription
from app.models.subscription import PaymentStatus
from app import db
from app.routes.admin.dashboard import admin_required
from datetime import datetime, timedelta

payments_bp = Blueprint('admin_payments', __name__, url_prefix='/admin/payments')


@payments_bp.route('/pending')
@login_required
@admin_required
def pending_payments():
    """Pagamentos pendentes de aprovação"""
    payments = Payment.query.filter(
        Payment.status == PaymentStatusEnum.PENDING,
        Payment.proof_url != None
    ).order_by(Payment.created_at.desc()).all()

    return render_template('admin/payments/pending.html', payments=payments)


@payments_bp.route('/overdue')
@login_required
@admin_required
def overdue_payments():
    """Pagamentos em atraso"""
    # Atualizar status de pagamentos atrasados
    today = datetime.now().date()
    overdue = Payment.query.filter(
        Payment.status == PaymentStatusEnum.PENDING,
        Payment.due_date < today
    ).all()

    for payment in overdue:
        payment.status = PaymentStatusEnum.OVERDUE
        payment.overdue_days = (today - payment.due_date).days

    db.session.commit()

    # Agrupar por dias de atraso
    payments_15days = Payment.query.filter(
        Payment.status == PaymentStatusEnum.OVERDUE,
        Payment.overdue_days >= 15,
        Payment.overdue_days < 90
    ).all()

    payments_90days = Payment.query.filter(
        Payment.status == PaymentStatusEnum.OVERDUE,
        Payment.overdue_days >= 90
    ).all()

    # Pagamentos recém-atrasados (até 15 dias)
    payments_recent = Payment.query.filter(
        Payment.status == PaymentStatusEnum.OVERDUE,
        Payment.overdue_days < 15
    ).all()

    return render_template('admin/payments/overdue.html',
                         payments_recent=payments_recent,
                         payments_15days=payments_15days,
                         payments_90days=payments_90days)


@payments_bp.route('/approve/<int:id>', methods=['POST'])
@login_required
@admin_required
def approve_payment(id):
    """Aprovar pagamento"""
    payment = Payment.query.get_or_404(id)
    subscription = payment.subscription

    # Marcar como pago
    payment.mark_as_paid()

    # Verificar se todas as parcelas foram pagas
    all_paid = all(p.status == PaymentStatusEnum.PAID for p in subscription.payments)

    if all_paid:
        subscription.payment_status = PaymentStatus.PAID
    else:
        subscription.payment_status = PaymentStatus.PARTIAL

    # Se estava bloqueada, desbloquear
    if subscription.is_blocked:
        subscription.unblock()

    db.session.commit()

    # Enviar confirmação WhatsApp (se configurado)
    try:
        from app.services.megaapi import megaapi
        megaapi.send_template_message(
            phone=subscription.user.phone,
            template_name='confirmacao_pagamento',
            variables=[
                subscription.user.name.split()[0],
                f'{payment.installment_number}/{payment.installment_total}',
                f'{payment.amount:.2f}',
                subscription.end_date.strftime('%d/%m/%Y'),
                current_app.config.get('ACADEMIA_NAME', 'Academia')
            ]
        )
    except Exception as e:
        flash(f'Pagamento aprovado, mas erro ao enviar WhatsApp: {str(e)}', 'warning')

    flash(f'Pagamento aprovado! Parcela {payment.installment_number}/{payment.installment_total}', 'success')
    return redirect(url_for('admin_payments.pending_payments'))


@payments_bp.route('/reject/<int:id>', methods=['POST'])
@login_required
@admin_required
def reject_payment(id):
    """Rejeitar comprovante"""
    payment = Payment.query.get_or_404(id)

    reason = request.form.get('reason', 'Comprovante inválido')

    # Manter como pendente, mas limpar comprovante
    payment.proof_url = None
    db.session.commit()

    # Enviar WhatsApp (se configurado)
    try:
        from app.services.megaapi import megaapi
        academia_name = current_app.config.get('ACADEMIA_NAME', 'Academia')
        megaapi.send_custom_message(
            phone=payment.subscription.user.phone,
            message=f"""Olá {payment.subscription.user.name.split()[0]},

O comprovante da parcela {payment.installment_number}/{payment.installment_total} foi rejeitado.

Motivo: {reason}

Por favor, envie um novo comprovante válido.

{academia_name}""".strip()
        )
    except:
        pass

    flash(f'Comprovante rejeitado. Aluno notificado.', 'warning')
    return redirect(url_for('admin_payments.pending_payments'))


@payments_bp.route('/send-reminders', methods=['POST'])
@login_required
@admin_required
def send_payment_reminders():
    """Enviar lembretes em massa de pagamentos atrasados"""
    # Pagamentos vencidos há 3 dias (primeira cobrança)
    three_days_ago = datetime.now().date() - timedelta(days=3)

    overdue = Payment.query.filter(
        Payment.status == PaymentStatusEnum.OVERDUE,
        Payment.due_date == three_days_ago
    ).all()

    sent = 0
    for payment in overdue:
        try:
            from app.services.megaapi import megaapi
            megaapi.send_template_message(
                phone=payment.subscription.user.phone,
                template_name='pagamento_atrasado',
                variables=[
                    payment.subscription.user.name.split()[0],
                    str(payment.overdue_days),
                    f'{payment.amount:.2f}',
                    f'{payment.installment_number}/{payment.installment_total}',
                    current_app.config.get('ACADEMIA_NAME', 'Academia')
                ]
            )
            sent += 1
        except:
            pass

    flash(f'{sent} lembrete(s) enviado(s)!', 'success')
    return redirect(url_for('admin_payments.overdue_payments'))


@payments_bp.route('/block-subscription/<int:subscription_id>', methods=['POST'])
@login_required
@admin_required
def block_subscription(subscription_id):
    """Bloquear assinatura por inadimplência"""
    subscription = Subscription.query.get_or_404(subscription_id)
    reason = request.form.get('reason', 'Inadimplência - pagamento em atraso')

    subscription.block(reason)

    # Notificar aluno
    try:
        from app.services.megaapi import megaapi
        academia_name = current_app.config.get('ACADEMIA_NAME', 'Academia')
        megaapi.send_custom_message(
            phone=subscription.user.phone,
            message=f"""Olá {subscription.user.name.split()[0]},

Sua assinatura foi SUSPENSA por inadimplência.

Motivo: {reason}

Para reativar, regularize seus pagamentos pendentes.

{academia_name}""".strip()
        )
    except:
        pass

    flash(f'Assinatura de {subscription.user.name} bloqueada.', 'warning')
    return redirect(url_for('admin_payments.overdue_payments'))


@payments_bp.route('/cancel-subscription/<int:subscription_id>', methods=['POST'])
@login_required
@admin_required
def cancel_subscription(subscription_id):
    """Cancelar assinatura (90+ dias de atraso)"""
    subscription = Subscription.query.get_or_404(subscription_id)

    subscription.cancel()

    # Notificar aluno
    try:
        from app.services.megaapi import megaapi
        academia_name = current_app.config.get('ACADEMIA_NAME', 'Academia')
        megaapi.send_custom_message(
            phone=subscription.user.phone,
            message=f"""Olá {subscription.user.name.split()[0]},

Sua assinatura foi CANCELADA por inadimplência superior a 90 dias.

Para retornar às atividades, será necessário adquirir um novo pacote.

{academia_name}""".strip()
        )
    except:
        pass

    flash(f'Assinatura de {subscription.user.name} cancelada.', 'danger')
    return redirect(url_for('admin_payments.overdue_payments'))


@payments_bp.route('/send-bulk-collection', methods=['POST'])
@login_required
@admin_required
def send_bulk_collection():
    """Enviar cobranças em massa por faixa de atraso."""
    range_filter = request.form.get('range', 'all')
    today = datetime.now().date()

    query = Payment.query.filter(Payment.status == PaymentStatusEnum.OVERDUE)

    if range_filter == '15d':
        query = query.filter(Payment.overdue_days >= 15, Payment.overdue_days < 30)
    elif range_filter == '30d':
        query = query.filter(Payment.overdue_days >= 30, Payment.overdue_days < 60)
    elif range_filter == '60d':
        query = query.filter(Payment.overdue_days >= 60, Payment.overdue_days < 90)
    elif range_filter == '90d':
        query = query.filter(Payment.overdue_days >= 90)

    payments = query.all()
    sent = 0
    errors = 0

    for payment in payments:
        if not payment.subscription or not payment.subscription.user or not payment.subscription.user.phone:
            errors += 1
            continue
        try:
            from app.services.megaapi import megaapi
            user = payment.subscription.user
            academia_name = current_app.config.get('ACADEMIA_NAME', 'Academia')
            megaapi.send_custom_message(
                phone=user.phone,
                message=f"Ola {user.name.split()[0]}, voce possui uma parcela em atraso "
                        f"({payment.installment_number}/{payment.installment_total}) no valor de "
                        f"R$ {payment.amount:.2f}, vencida ha {payment.overdue_days} dias. "
                        f"Regularize para manter seu acesso. {academia_name}"
            )
            sent += 1
        except Exception:
            errors += 1

    flash(f'Cobranças enviadas: {sent} sucesso, {errors} erros.', 'success' if errors == 0 else 'warning')
    return redirect(url_for('admin_payments.overdue_payments'))


@payments_bp.route('/receipt/<int:payment_id>')
@login_required
@admin_required
def generate_receipt(payment_id):
    """Gerar recibo PDF para pagamento aprovado."""
    from flask import make_response
    payment = Payment.query.get_or_404(payment_id)

    if payment.status != PaymentStatusEnum.PAID:
        flash('Recibo so pode ser gerado para pagamentos aprovados.', 'warning')
        return redirect(url_for('admin_payments.pending_payments'))

    user = payment.subscription.user
    package = payment.subscription.package

    # Gerar PDF simples com reportlab-like approach
    pdf_bytes = _generate_receipt_pdf(payment, user, package)

    response = make_response(pdf_bytes)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=recibo_{payment.id}.pdf'
    return response


@payments_bp.route('/receipt/<int:payment_id>/send', methods=['POST'])
@login_required
@admin_required
def send_receipt_whatsapp(payment_id):
    """Enviar recibo via WhatsApp."""
    payment = Payment.query.get_or_404(payment_id)

    if payment.status != PaymentStatusEnum.PAID:
        flash('Recibo so pode ser enviado para pagamentos aprovados.', 'warning')
        return redirect(url_for('admin_payments.pending_payments'))

    user = payment.subscription.user
    try:
        from app.services.megaapi import megaapi
        academia_name = current_app.config.get('ACADEMIA_NAME', 'Academia')
        megaapi.send_custom_message(
            phone=user.phone,
            message=f"Ola {user.name.split()[0]}! Confirmamos o recebimento do seu pagamento.\n\n"
                    f"Parcela: {payment.installment_number}/{payment.installment_total}\n"
                    f"Valor: R$ {payment.amount:.2f}\n"
                    f"Data: {payment.paid_date.strftime('%d/%m/%Y') if payment.paid_date else '-'}\n\n"
                    f"Obrigado! {academia_name}"
        )
        flash('Recibo enviado via WhatsApp!', 'success')
    except Exception as e:
        flash(f'Erro ao enviar: {str(e)}', 'danger')

    return redirect(url_for('admin_payments.overdue_payments'))


def _generate_receipt_pdf(payment, user, package):
    """Gera PDF de recibo simples."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import cm
        from reportlab.pdfgen import canvas as pdf_canvas
        from reportlab.lib.colors import HexColor
        import io

        buffer = io.BytesIO()
        c = pdf_canvas.Canvas(buffer, pagesize=A4)
        w, h = A4

        # Header
        c.setFillColor(HexColor('#1a1a2e'))
        c.rect(0, h - 100, w, 100, fill=True)
        c.setFillColor(HexColor('#ffffff'))
        c.setFont('Helvetica-Bold', 20)
        c.drawCentredString(w / 2, h - 50, 'RECIBO DE PAGAMENTO')
        c.setFont('Helvetica', 11)
        c.drawCentredString(w / 2, h - 72, f'No. {payment.id:06d}')

        y = h - 140
        c.setFillColor(HexColor('#333333'))

        # Dados do aluno
        c.setFont('Helvetica-Bold', 12)
        c.drawString(2 * cm, y, 'DADOS DO ALUNO')
        y -= 20
        c.setFont('Helvetica', 10)
        c.drawString(2 * cm, y, f'Nome: {user.name}')
        y -= 16
        c.drawString(2 * cm, y, f'Email: {user.email or "-"}')
        y -= 16
        c.drawString(2 * cm, y, f'Telefone: {user.phone or "-"}')

        y -= 35
        c.setFont('Helvetica-Bold', 12)
        c.drawString(2 * cm, y, 'DADOS DO PAGAMENTO')
        y -= 20
        c.setFont('Helvetica', 10)
        c.drawString(2 * cm, y, f'Pacote: {package.name if package else "-"}')
        y -= 16
        c.drawString(2 * cm, y, f'Parcela: {payment.installment_number}/{payment.installment_total}')
        y -= 16
        c.drawString(2 * cm, y, f'Valor: R$ {payment.amount:.2f}')
        y -= 16
        c.drawString(2 * cm, y, f'Vencimento: {payment.due_date.strftime("%d/%m/%Y") if payment.due_date else "-"}')
        y -= 16
        c.drawString(2 * cm, y, f'Data Pagamento: {payment.paid_date.strftime("%d/%m/%Y") if payment.paid_date else "-"}')
        y -= 16
        c.drawString(2 * cm, y, f'Metodo: {payment.payment_method or "Manual"}')

        # Valor destaque
        y -= 40
        c.setFillColor(HexColor('#198754'))
        c.setFont('Helvetica-Bold', 16)
        c.drawCentredString(w / 2, y, f'VALOR PAGO: R$ {payment.amount:.2f}')

        # Footer
        c.setFillColor(HexColor('#999999'))
        c.setFont('Helvetica', 8)
        c.drawCentredString(w / 2, 2 * cm, f'Gerado em {datetime.now().strftime("%d/%m/%Y %H:%M")} - Documento sem valor fiscal')

        c.save()
        return buffer.getvalue()

    except ImportError:
        # Fallback sem reportlab - gera HTML simples convertido a texto
        html = f"""
        <h1>RECIBO DE PAGAMENTO #{payment.id:06d}</h1>
        <p>Aluno: {user.name}</p>
        <p>Pacote: {package.name if package else '-'}</p>
        <p>Parcela: {payment.installment_number}/{payment.installment_total}</p>
        <p>Valor: R$ {payment.amount:.2f}</p>
        <p>Data: {payment.paid_date.strftime('%d/%m/%Y') if payment.paid_date else '-'}</p>
        """
        return html.encode('utf-8')
