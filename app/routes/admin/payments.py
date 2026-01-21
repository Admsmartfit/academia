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
