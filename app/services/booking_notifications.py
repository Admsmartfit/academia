# app/services/booking_notifications.py
"""
Notificações internas e WhatsApp para eventos de agendamento.
Cada função é silenciosa em caso de erro — nunca quebra o fluxo principal.
"""

import logging
from app import db
from app.models.notification import Notification, NotificationType

logger = logging.getLogger(__name__)


def _send_whatsapp(booking, message: str) -> bool:
    """Dispara mensagem WhatsApp se o usuário tiver telefone configurado."""
    try:
        if not booking.user or not booking.user.phone:
            return False
        from app.services.megaapi import megaapi
        megaapi.send_message(
            phone=booking.user.phone,
            message=message,
            user_id=booking.user_id,
        )
        return True
    except Exception as e:
        logger.warning(f"[booking_notifications] WhatsApp falhou booking={booking.id}: {e}")
        return False


def notify_booking_confirmed(booking) -> None:
    """
    Dispara ao criar um Booking CONFIRMED (avulso ou primeiro da recorrência).
    Cria Notification interna + envia WhatsApp se telefone disponível.
    """
    try:
        schedule = booking.schedule
        date_fmt = booking.date.strftime('%d/%m/%Y')
        time_fmt = schedule.start_time.strftime('%H:%M') if schedule else '?'
        modality = schedule.modality.name if schedule and schedule.modality else 'Aula'

        # Notificação interna
        Notification.create(
            user_id=booking.user_id,
            notification_type=NotificationType.CLASS_REMINDER,
            title=f'Aula confirmada — {modality}',
            message=f'{date_fmt} às {time_fmt}. Boa aula!',
            link='/student/my-bookings',
        )
        db.session.commit()

        # WhatsApp
        first_name = booking.user.name.split()[0] if booking.user else 'Aluno'
        _send_whatsapp(booking, (
            f"✅ *Aula confirmada!*\n"
            f"Olá {first_name}, sua aula está agendada.\n\n"
            f"📅 {date_fmt} às {time_fmt}\n"
            f"🏋️ {modality}\n\n"
            f"Para cancelar acesse o app."
        ))
    except Exception as e:
        logger.error(f"[booking_notifications] notify_booking_confirmed erro: {e}")


def notify_booking_cancelled(booking, cancelled_by: str = 'client') -> None:
    """
    Dispara ao cancelar um Booking.
    cancelled_by: 'client' | 'provider' | 'system'
    """
    try:
        schedule = booking.schedule
        date_fmt = booking.date.strftime('%d/%m/%Y')
        time_fmt = schedule.start_time.strftime('%H:%M') if schedule else '?'
        modality = schedule.modality.name if schedule and schedule.modality else 'Aula'

        if cancelled_by == 'client':
            title = f'Aula cancelada — {modality}'
            msg = f'Você cancelou sua aula de {modality} em {date_fmt} às {time_fmt}. Crédito estornado.'
            wa_msg = (
                f"❌ *Aula cancelada*\n"
                f"{modality} — {date_fmt} às {time_fmt}\n"
                f"Seu crédito foi estornado."
            )
        else:
            title = f'Aula cancelada pelo instrutor — {modality}'
            msg = f'A aula de {modality} em {date_fmt} às {time_fmt} foi cancelada. Crédito estornado.'
            wa_msg = (
                f"⚠️ *Aula cancelada pelo instrutor*\n"
                f"{modality} — {date_fmt} às {time_fmt}\n"
                f"Lamentamos o inconveniente. Seu crédito foi estornado."
            )

        Notification.create(
            user_id=booking.user_id,
            notification_type=NotificationType.GENERAL,
            title=title,
            message=msg,
            link='/student/my-bookings',
        )
        db.session.commit()

        _send_whatsapp(booking, wa_msg)
    except Exception as e:
        logger.error(f"[booking_notifications] notify_booking_cancelled erro: {e}")


def notify_no_show(booking) -> None:
    """
    Dispara quando booking vira NO_SHOW — para followup de retenção.
    """
    try:
        schedule = booking.schedule
        date_fmt = booking.date.strftime('%d/%m/%Y')
        modality = schedule.modality.name if schedule and schedule.modality else 'Aula'

        Notification.create(
            user_id=booking.user_id,
            notification_type=NotificationType.GENERAL,
            title=f'Você faltou — {modality}',
            message=f'Registramos sua falta na aula de {modality} em {date_fmt}. Que tal reagendar?',
            link='/student/schedule',
        )
        db.session.commit()

        first_name = booking.user.name.split()[0] if booking.user else 'Aluno'
        _send_whatsapp(booking, (
            f"😕 Olá {first_name}, sentimos sua falta!\n\n"
            f"Você não compareceu à aula de *{modality}* em {date_fmt}.\n"
            f"Que tal agendar uma nova aula? Acesse o app e escolha seu horário."
        ))
    except Exception as e:
        logger.error(f"[booking_notifications] notify_no_show erro: {e}")
