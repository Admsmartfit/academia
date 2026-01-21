# app/services/payment_processor.py

from datetime import datetime, timedelta
from app.models import Payment, Subscription, PaymentStatusEnum, SubscriptionStatus
from app import db


class PaymentProcessor:
    """
    Gerencia logica de pagamentos e cobrancas
    """

    @staticmethod
    def process_overdue_payments():
        """
        Processa pagamentos atrasados e aplica bloqueios
        Executado diariamente via scheduler
        """
        today = datetime.now().date()

        # Buscar pagamentos atrasados
        overdue_payments = Payment.query.filter(
            Payment.status.in_([PaymentStatusEnum.PENDING, PaymentStatusEnum.OVERDUE]),
            Payment.due_date < today
        ).all()

        for payment in overdue_payments:
            days_overdue = (today - payment.due_date).days
            payment.overdue_days = days_overdue

            subscription = payment.subscription

            # Regra 1: 15 dias = Bloquear agenda
            if days_overdue == 15:
                subscription.block(f"Pagamento atrasado ha 15 dias (Parcela {payment.installment_number}/{payment.installment_total})")

                # Enviar WhatsApp
                try:
                    from app.services.megaapi import megaapi

                    megaapi.send_template_message(
                        phone=subscription.user.phone,
                        template_name='assinatura_bloqueada',
                        variables=[
                            subscription.user.name.split()[0],
                            str(days_overdue),
                            f'{payment.amount:.2f}',
                            subscription.package.name
                        ],
                        user_id=subscription.user_id
                    )
                except Exception as e:
                    print(f"Erro ao enviar WhatsApp bloqueio: {e}")

            # Regra 2: 90 dias = Cancelar creditos
            elif days_overdue == 90:
                subscription.cancel()

                # Enviar WhatsApp
                try:
                    from app.services.megaapi import megaapi

                    megaapi.send_template_message(
                        phone=subscription.user.phone,
                        template_name='assinatura_cancelada',
                        variables=[
                            subscription.user.name.split()[0],
                            subscription.package.name,
                            str(subscription.credits_total)
                        ],
                        user_id=subscription.user_id
                    )
                except Exception as e:
                    print(f"Erro ao enviar WhatsApp cancelamento: {e}")

            # Atualizar status
            if payment.status != PaymentStatusEnum.OVERDUE:
                payment.status = PaymentStatusEnum.OVERDUE

        db.session.commit()

        print(f"[PAYMENT PROCESSOR] Processados {len(overdue_payments)} pagamentos atrasados")
        return len(overdue_payments)

    @staticmethod
    def send_upcoming_payment_reminders():
        """
        Envia lembretes 3 dias antes do vencimento
        """
        three_days_from_now = datetime.now().date() + timedelta(days=3)

        upcoming_payments = Payment.query.filter(
            Payment.status == PaymentStatusEnum.PENDING,
            Payment.due_date == three_days_from_now
        ).all()

        sent_count = 0
        for payment in upcoming_payments:
            try:
                from app.services.megaapi import megaapi

                megaapi.send_template_message(
                    phone=payment.subscription.user.phone,
                    template_name='lembrete_pagamento',
                    variables=[
                        payment.subscription.user.name.split()[0],
                        f'{payment.installment_number}/{payment.installment_total}',
                        payment.due_date.strftime('%d/%m/%Y'),
                        f'{payment.amount:.2f}',
                        '3'  # dias restantes
                    ],
                    user_id=payment.subscription.user_id
                )
                sent_count += 1
            except Exception as e:
                print(f"Erro ao enviar lembrete: {e}")

        print(f"[PAYMENT PROCESSOR] Enviados {sent_count} lembretes de pagamento")
        return sent_count

    @staticmethod
    def expire_old_credits():
        """
        Expira creditos nao utilizados apos validade
        """
        today = datetime.now().date()

        expired_subscriptions = Subscription.query.filter(
            Subscription.end_date < today,
            Subscription.status == SubscriptionStatus.ACTIVE,
            (Subscription.credits_total - Subscription.credits_used) > 0
        ).all()

        for subscription in expired_subscriptions:
            # Guardar creditos perdidos
            credits_lost = subscription.credits_total - subscription.credits_used

            # Zerar creditos
            subscription.credits_used = subscription.credits_total
            subscription.status = SubscriptionStatus.EXPIRED

            # Notificar
            try:
                from app.services.megaapi import megaapi

                megaapi.send_template_message(
                    phone=subscription.user.phone,
                    template_name='creditos_expirados',
                    variables=[
                        subscription.user.name.split()[0],
                        str(credits_lost),
                        subscription.package.name
                    ],
                    user_id=subscription.user_id
                )
            except Exception as e:
                print(f"Erro ao notificar expiracao: {e}")

        db.session.commit()

        print(f"[PAYMENT PROCESSOR] Expiradas {len(expired_subscriptions)} assinaturas")
        return len(expired_subscriptions)

    @staticmethod
    def mark_as_paid(payment_id, approved_by_id=None):
        """
        Marca pagamento como pago e atualiza assinatura
        """
        payment = Payment.query.get(payment_id)
        if not payment:
            return False, "Pagamento nao encontrado"

        if payment.status == PaymentStatusEnum.PAID:
            return False, "Pagamento ja foi aprovado"

        # Atualizar pagamento
        payment.status = PaymentStatusEnum.PAID
        payment.paid_at = datetime.utcnow()
        payment.approved_by_id = approved_by_id
        payment.overdue_days = 0

        subscription = payment.subscription

        # Verificar se todas as parcelas estao pagas
        all_paid = all(
            p.status == PaymentStatusEnum.PAID
            for p in subscription.payments
        )

        if all_paid:
            subscription.payment_status = SubscriptionStatus.ACTIVE

        # Desbloquear se estava bloqueado
        if subscription.is_blocked:
            subscription.unblock()

        db.session.commit()

        # Enviar confirmacao WhatsApp
        try:
            from app.services.megaapi import megaapi

            megaapi.send_template_message(
                phone=subscription.user.phone,
                template_name='pagamento_confirmado',
                variables=[
                    subscription.user.name.split()[0],
                    f'{payment.installment_number}/{payment.installment_total}',
                    f'{payment.amount:.2f}',
                    subscription.package.name
                ],
                user_id=subscription.user_id
            )
        except Exception as e:
            print(f"Erro ao enviar confirmacao WhatsApp: {e}")

        return True, "Pagamento aprovado com sucesso"


# Singleton
payment_processor = PaymentProcessor()
