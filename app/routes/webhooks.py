# app/routes/webhooks.py

import os
from flask import Blueprint, request, jsonify, current_app
from app.models import WhatsAppLog, Payment, User, Booking, BookingStatus
from app.models.payment import PaymentStatusEnum
from app.models.crm import AutomationLog
from app import db
from datetime import datetime
import hmac
import hashlib
import logging

logger = logging.getLogger(__name__)

webhooks_bp = Blueprint('webhooks', __name__, url_prefix='/webhooks')


# ============================================================
# NUPAY WEBHOOK
# ============================================================

def validate_nupay_signature(req):
    """
    Valida HMAC-SHA256 do webhook NuPay.
    """
    signature = req.headers.get('X-NuPay-Signature')

    if not signature:
        logger.warning("Webhook NuPay recebido sem assinatura")
        return False

    secret = current_app.config.get('NUPAY_WEBHOOK_SECRET', '')

    if not secret:
        logger.warning("NUPAY_WEBHOOK_SECRET nao configurado - aceitando sem validacao")
        return True

    payload = req.get_data()

    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    is_valid = hmac.compare_digest(signature, expected)

    if not is_valid:
        logger.warning(f"Assinatura NuPay invalida. Recebida: {signature[:20]}...")

    return is_valid


@webhooks_bp.route('/nupay/callback', methods=['POST'])
def nupay_callback():
    """
    Recebe callbacks da NuPay sobre status de pagamentos.
    """
    try:
        if not validate_nupay_signature(request):
            logger.error("Webhook NuPay: assinatura invalida")
            return jsonify({"error": "Invalid signature"}), 401

        data = request.get_json()

        if not data:
            logger.error("Webhook NuPay: payload vazio")
            return jsonify({"error": "No data received"}), 400

        merchant_reference = data.get('merchantReferenceId', '')
        psp_reference = data.get('pspReferenceId', '')
        status = data.get('status', '')

        logger.info(f"Webhook NuPay recebido: {merchant_reference} - Status: {status}")

        payment = Payment.query.filter_by(nupay_reference_id=merchant_reference).first()

        if not payment:
            try:
                if merchant_reference.startswith('PAYMENT_'):
                    payment_id = int(merchant_reference.replace('PAYMENT_', ''))
                    payment = Payment.query.get(payment_id)
            except (ValueError, TypeError):
                pass

        if not payment:
            logger.warning(f"Webhook NuPay: Payment nao encontrado para {merchant_reference}")
            return jsonify({"error": "Payment not found"}), 404

        if psp_reference and not payment.nupay_psp_reference_id:
            payment.nupay_psp_reference_id = psp_reference

        if status == 'COMPLETED':
            _process_payment_completed(payment, data)
        elif status == 'FAILED':
            _process_payment_failed(payment, data)
        elif status == 'CANCELLED':
            payment.status = PaymentStatusEnum.CANCELLED
            logger.info(f"Payment #{payment.id} marcado como cancelado")
        elif status == 'EXPIRED':
            logger.info(f"Payment #{payment.id}: PIX expirou")
        else:
            logger.warning(f"Webhook NuPay: status desconhecido '{status}'")

        db.session.commit()

        return jsonify({"status": "ok"}), 200

    except Exception as e:
        logger.error(f"Erro no webhook NuPay: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


def _process_payment_completed(payment, data):
    """Processa pagamento confirmado."""
    payment.mark_as_paid()
    logger.info(f"Payment #{payment.id} marcado como PAID")

    subscription = payment.subscription
    user = subscription.user
    package = subscription.package

    if subscription.is_blocked:
        subscription.unblock()
        logger.info(f"Subscription #{subscription.id} desbloqueada")

    if payment.installment_number == 1:
        xp_bonus = package.welcome_xp_bonus or 0
        if xp_bonus > 0:
            user.add_xp(xp_bonus)
            logger.info(f"User #{user.id} recebeu {xp_bonus} XP de boas-vindas")

    try:
        from app.services.megaapi import megaapi, Button

        first_name = user.name.split()[0] if user.name else 'Cliente'
        credits = subscription.credits_remaining
        validade = subscription.end_date.strftime('%d/%m/%Y')

        buttons = [
            Button(id='view_schedule', title='Ver horários'),
            Button(id='book_first_class', title='Agendar primeira aula')
        ]

        megaapi.send_buttons(
            phone=user.phone,
            message=(f"Pagamento confirmado! Você tem *{credits}* créditos "
                     f"até *{validade}*. Bora treinar!"),
            buttons=buttons,
            user_id=user.id
        )
    except Exception as e:
        logger.error(f"Erro ao enviar WhatsApp de confirmacao: {str(e)}")


def _process_payment_failed(payment, data):
    """Processa pagamento que falhou."""
    payment.status = PaymentStatusEnum.PENDING
    logger.info(f"Payment #{payment.id} marcado como falha - voltou para PENDING")

    try:
        from app.services.megaapi import megaapi

        user = payment.subscription.user
        first_name = user.name.split()[0] if user.name else 'Cliente'

        megaapi.send_custom_message(
            phone=user.phone,
            message=f"Ola {first_name}, houve um problema com seu pagamento. "
                    f"Por favor, tente novamente ou entre em contato conosco.",
            user_id=user.id
        )
    except Exception as e:
        logger.error(f"Erro ao enviar WhatsApp de falha: {str(e)}")


@webhooks_bp.route('/nupay/subscription', methods=['POST'])
def nupay_subscription_callback():
    """Recebe callbacks da NuPay sobre assinaturas recorrentes."""
    try:
        if not validate_nupay_signature(request):
            return jsonify({"error": "Invalid signature"}), 401

        data = request.get_json()

        if not data:
            return jsonify({"error": "No data received"}), 400

        subscription_id = data.get('subscriptionId', '')
        event = data.get('event', '')

        logger.info(f"Webhook NuPay Subscription: {subscription_id} - Event: {event}")

        from app.models import Subscription

        subscription = Subscription.query.filter_by(
            nupay_subscription_id=subscription_id
        ).first()

        if not subscription:
            logger.warning(f"Subscription nao encontrada: {subscription_id}")
            return jsonify({"error": "Subscription not found"}), 404

        if event == 'SUBSCRIPTION_RENEWED':
            _process_subscription_renewed(subscription, data)
        elif event == 'SUBSCRIPTION_CANCELLED':
            subscription.recurring_status = 'CANCELLED'
            subscription.is_recurring = False
            logger.info(f"Subscription #{subscription.id} recorrencia cancelada")
        elif event == 'SUBSCRIPTION_PAUSED':
            subscription.recurring_status = 'PAUSED'
            logger.info(f"Subscription #{subscription.id} recorrencia pausada")

        db.session.commit()

        return jsonify({"status": "ok"}), 200

    except Exception as e:
        logger.error(f"Erro no webhook NuPay Subscription: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


def _process_subscription_renewed(subscription, data):
    """Processa renovacao de assinatura recorrente."""
    from datetime import date, timedelta

    package = subscription.package
    user = subscription.user

    new_payment = Payment(
        subscription_id=subscription.id,
        installment_number=1,
        installment_total=1,
        amount=package.price,
        due_date=date.today(),
        status=PaymentStatusEnum.PAID,
        paid_date=datetime.utcnow(),
        payment_method='nupay_recurring',
        nupay_psp_reference_id=data.get('paymentId', '')
    )
    db.session.add(new_payment)

    subscription.credits_total += package.credits
    subscription.last_billing_date = date.today()
    subscription.next_billing_date = date.today() + timedelta(
        days=package.recurring_interval_days or 30
    )
    subscription.end_date = date.today() + timedelta(days=package.validity_days)

    logger.info(f"Subscription #{subscription.id} renovada: +{package.credits} creditos")

    try:
        from app.services.megaapi import megaapi

        first_name = user.name.split()[0] if user.name else 'Cliente'

        megaapi.send_custom_message(
            phone=user.phone,
            message=f"Ola {first_name}! Sua assinatura foi renovada automaticamente. "
                    f"+{package.credits} creditos adicionados! "
                    f"Total disponivel: {subscription.credits_remaining} creditos.",
            user_id=user.id
        )
    except Exception as e:
        logger.error(f"Erro ao enviar WhatsApp de renovacao: {str(e)}")


# ============================================================
# MEGAAPI WEBHOOK - STATUS DE MENSAGENS
# ============================================================

def validate_megaapi_signature(req):
    """
    Valida HMAC-SHA256 do webhook MegaAPI.
    Previne webhooks falsificados.
    """
    secret = os.getenv('MEGAAPI_WEBHOOK_SECRET', '')

    if not secret:
        logger.warning("MEGAAPI_WEBHOOK_SECRET nao configurado - aceitando sem validacao")
        return True

    signature = req.headers.get('X-MegaAPI-Signature')
    if not signature:
        return False

    payload = req.get_data()
    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(signature, expected)


@webhooks_bp.route('/megaapi', methods=['POST'])
def megaapi_webhook():
    """
    Recebe callbacks da Megaapi sobre status de mensagens.

    Eventos:
    - message_sent / message.status(sent)
    - message_delivered / message.status(delivered)
    - message_read / message.status(read)
    - message_failed / message.status(failed)
    """
    try:
        if not validate_megaapi_signature(request):
            logger.warning("Webhook MegaAPI com assinatura invalida")
            return jsonify({'error': 'Invalid signature'}), 401

        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data received'}), 400

        # Suportar ambos os formatos de evento
        event_type = data.get('event') or data.get('type', '')
        message_id = data.get('message_id') or data.get('messageId')
        status = data.get('status', '')

        if not message_id and not status:
            return jsonify({'error': 'No message_id or status'}), 400

        # Buscar log da mensagem
        log = None
        if message_id:
            log = WhatsAppLog.query.filter_by(message_id=message_id).first()

        if not log:
            log = WhatsAppLog(
                message_id=message_id,
                phone=data.get('phone', data.get('from', '')),
                template_name=data.get('template_name', 'unknown'),
                status='pending'
            )
            db.session.add(log)

        # Determinar status final
        final_status = status or event_type
        if final_status in ('message_sent', 'sent'):
            log.status = 'sent'
        elif final_status in ('message_delivered', 'delivered'):
            log.status = 'delivered'
            log.delivered_at = datetime.utcnow()
        elif final_status in ('message_read', 'read'):
            log.status = 'read'
            log.read_at = datetime.utcnow()
        elif final_status in ('message_failed', 'failed'):
            log.status = 'failed'
            log.error_message = data.get('error', 'Unknown error')

        log.response_json = data

        db.session.commit()

        return jsonify({'status': 'ok'}), 200

    except Exception as e:
        logger.error(f"Erro no webhook Megaapi: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================================
# MEGAAPI WEBHOOK - MENSAGENS RECEBIDAS (INTERATIVAS)
# ============================================================

@webhooks_bp.route('/megaapi/incoming', methods=['POST'])
def megaapi_incoming():
    """
    Recebe mensagens de entrada (respostas dos clientes).

    Tipos processados:
    - buttonsResponseMessage: Clique em botao
    - listResponseMessage: Selecao em lista
    - conversation (texto): Mensagem de texto livre
    """
    try:
        if not validate_megaapi_signature(request):
            logger.warning("Webhook incoming MegaAPI com assinatura invalida")
            return jsonify({'error': 'Invalid signature'}), 401

        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data received'}), 400

        phone = data.get('from', '')
        message = data.get('message', {})

        logger.info(f"Webhook incoming de {phone}: {list(message.keys()) if message else 'vazio'}")

        # 1. Resposta de botao (Button Reply)
        if 'buttonsResponseMessage' in message:
            _handle_button_reply(phone, message['buttonsResponseMessage'])

        # 2. Resposta de lista (List Reply)
        elif 'listResponseMessage' in message:
            _handle_list_reply(phone, message['listResponseMessage'])

        # 3. Mensagem de texto livre
        elif message.get('text') or message.get('conversation'):
            text = message.get('text', '') or message.get('conversation', '')
            _handle_text_message(phone, text)

        else:
            logger.info(f"Tipo de mensagem nao tratado de {phone}")

        # Log da mensagem recebida
        log = WhatsAppLog(
            phone=phone,
            template_name='incoming_message',
            status='received',
            response_json=data,
            sent_at=datetime.utcnow()
        )
        db.session.add(log)
        db.session.commit()

        return jsonify({'status': 'ok'}), 200

    except Exception as e:
        logger.error(f"Erro no webhook incoming: {e}", exc_info=True)
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ============================================================
# HANDLERS DE RESPOSTAS INTERATIVAS
# ============================================================

def _handle_button_reply(phone, button_data):
    """
    Processa clique em botao.

    Payload:
    {
        "selectedButtonId": "confirm_123",
        "selectedDisplayText": "Vou comparecer"
    }
    """
    button_id = button_data.get('selectedButtonId', '')
    logger.info(f"Botao clicado: {button_id} por {phone}")

    if not button_id:
        return

    # Parse do button_id: action_param
    parts = button_id.split('_', 1)
    action = parts[0]
    param = parts[1] if len(parts) > 1 else ''

    from app.services.megaapi import megaapi, Button

    # --- Acoes de booking ---
    if action == 'confirm' and param:
        _confirm_booking_attendance(int(param), phone)

    elif action == 'cancel' and param:
        _cancel_booking_via_whatsapp(int(param), phone)

    elif action == 'reschedule':
        _send_available_slots(phone)

    # --- Acoes de retencao ---
    elif action in ('yes', 'tomorrow') or button_id == 'yes_tomorrow':
        user = User.query.filter_by(phone=phone).first()
        if user:
            megaapi.send_custom_message(
                phone=phone,
                message="Que otimo! Te esperamos amanha! Bora treinar!",
                user_id=user.id
            )
            _log_button_interaction(user.id, button_id)

    elif button_id == 'reschedule_me':
        _send_available_slots(phone)

    elif button_id == 'im_ok':
        user = User.query.filter_by(phone=phone).first()
        if user:
            megaapi.send_custom_message(
                phone=phone,
                message="Que bom saber! Quando estiver pronto(a) para voltar, estamos aqui!",
                user_id=user.id
            )
            _log_button_interaction(user.id, button_id)

    elif button_id == 'talk_to_instructor':
        user = User.query.filter_by(phone=phone).first()
        if user:
            megaapi.send_custom_message(
                phone=phone,
                message="Vou pedir para seu instrutor entrar em contato com voce. Aguarde!",
                user_id=user.id
            )
            _log_button_interaction(user.id, button_id)

    elif button_id == 'free_personal':
        user = User.query.filter_by(phone=phone).first()
        if user:
            megaapi.send_custom_message(
                phone=phone,
                message="Sessao gratis de personal confirmada! "
                        "Nossa equipe vai entrar em contato para agendar o melhor horario.",
                user_id=user.id
            )
            _log_button_interaction(user.id, button_id)

    elif button_id == 'schedule_now':
        _send_available_slots(phone)

    elif button_id == 'claim_discount':
        user = User.query.filter_by(phone=phone).first()
        if user:
            megaapi.send_custom_message(
                phone=phone,
                message="Desconto de 30% ativado! "
                        "Nossa equipe vai entrar em contato para finalizar sua renovacao.",
                user_id=user.id
            )
            _log_button_interaction(user.id, button_id)

    elif button_id == 'schedule_call':
        user = User.query.filter_by(phone=phone).first()
        if user:
            megaapi.send_custom_message(
                phone=phone,
                message="Ligacao agendada! Nossa equipe vai ligar para voce em breve.",
                user_id=user.id
            )
            _log_button_interaction(user.id, button_id)

    elif button_id == 'cancel_membership':
        user = User.query.filter_by(phone=phone).first()
        if user:
            megaapi.send_custom_message(
                phone=phone,
                message="Lamentamos ouvir isso. Um consultor vai entrar em contato "
                        "para entender melhor e ver como podemos ajudar.",
                user_id=user.id
            )
            _log_button_interaction(user.id, button_id)

    # --- Acoes de boas-vindas ---
    elif button_id == 'facial_tutorial':
        user = User.query.filter_by(phone=phone).first()
        if user:
            megaapi.send_custom_message(
                phone=phone,
                message="Para cadastrar seu rosto:\n"
                        "1. Acesse seu perfil no app\n"
                        "2. Clique em 'Cadastrar Face'\n"
                        "3. Tire uma foto olhando para a camera\n"
                        "4. Pronto! Agora e so chegar no totem e sorrir!",
                user_id=user.id
            )

    elif button_id == 'schedule_evaluation':
        user = User.query.filter_by(phone=phone).first()
        if user:
            megaapi.send_custom_message(
                phone=phone,
                message="Para agendar sua avaliacao fisica, fale com a recepcao "
                        "ou acesse o app e va em 'Agendar Avaliacao'. "
                        "Te esperamos!",
                user_id=user.id
            )

    elif button_id == 'view_training':
        user = User.query.filter_by(phone=phone).first()
        if user:
            megaapi.send_custom_message(
                phone=phone,
                message="Acesse seu treino em: /student/my-training\n"
                        "La voce encontra todos os exercicios do dia com videos!",
                user_id=user.id
            )

    # --- PRD: Recuperação D+10 ---
    elif button_id == 'need_help':
        user = User.query.filter_by(phone=phone).first()
        if user:
            megaapi.send_custom_message(
                phone=phone,
                message="Entendemos! Um instrutor vai entrar em contato "
                        "para te ajudar a montar um plano que funcione "
                        "na sua rotina. Aguarde!",
                user_id=user.id
            )
            _log_button_interaction(user.id, button_id)

    elif button_id == 'pause_plan':
        user = User.query.filter_by(phone=phone).first()
        if user:
            megaapi.send_custom_message(
                phone=phone,
                message="Pedido de pausa recebido. Um consultor vai entrar "
                        "em contato para formalizar a pausa do seu plano.",
                user_id=user.id
            )
            _log_button_interaction(user.id, button_id)

    # --- PRD: Renovação de Plano ---
    elif button_id == 'renew_pix':
        user = User.query.filter_by(phone=phone).first()
        if user:
            megaapi.send_custom_message(
                phone=phone,
                message="Acesse a loja para renovar seu plano via PIX:\n"
                        "/shop/packages\n\n"
                        "É rápido e seus créditos são liberados na hora!",
                user_id=user.id
            )
            _log_button_interaction(user.id, button_id)

    elif button_id == 'talk_consultant':
        user = User.query.filter_by(phone=phone).first()
        if user:
            megaapi.send_custom_message(
                phone=phone,
                message="Um consultor vai entrar em contato em breve "
                        "para te ajudar com a renovação!",
                user_id=user.id
            )
            _log_button_interaction(user.id, button_id)

    elif button_id == 'remind_tomorrow':
        user = User.query.filter_by(phone=phone).first()
        if user:
            megaapi.send_custom_message(
                phone=phone,
                message="Ok! Vamos te lembrar amanhã sobre a renovação.",
                user_id=user.id
            )
            _log_button_interaction(user.id, button_id)

    # --- PRD: Pagamento Confirmado ---
    elif button_id == 'view_schedule':
        _send_available_slots(phone)

    elif button_id == 'book_first_class':
        _send_available_slots(phone)

    # --- PRD: Lembrete 2h - confirm_attendance ---
    elif button_id == 'confirm_attendance':
        user = User.query.filter_by(phone=phone).first()
        if user:
            megaapi.send_custom_message(
                phone=phone,
                message="Presença confirmada! Te esperamos na aula!",
                user_id=user.id
            )
            _log_button_interaction(user.id, button_id)

    # --- Satisfacao ---
    elif button_id.startswith('satisfaction_') and param:
        try:
            rating = int(param)
            _record_satisfaction_rating(phone, rating)
        except ValueError:
            pass

    else:
        logger.info(f"Acao de botao nao reconhecida: {button_id}")


def _handle_list_reply(phone, list_data):
    """
    Processa selecao de item em lista.

    Payload:
    {
        "singleSelectReply": {
            "selectedRowId": "slot_5"
        },
        "title": "15:00",
        "description": "Treino Funcional"
    }
    """
    row_id = list_data.get('singleSelectReply', {}).get('selectedRowId', '')
    if not row_id:
        row_id = list_data.get('selectedRowId', '')

    logger.info(f"Item de lista selecionado: {row_id} por {phone}")

    if not row_id:
        return

    parts = row_id.split('_', 1)
    action = parts[0]
    param = parts[1] if len(parts) > 1 else ''

    from app.services.megaapi import megaapi

    if action == 'confirm' and param:
        _confirm_booking_attendance(int(param), phone)

    elif action == 'cancel' and param:
        _cancel_booking_via_whatsapp(int(param), phone)

    elif action == 'slot' and param:
        _book_slot_via_whatsapp(int(param), phone)

    elif action == 'satisfaction' and param:
        try:
            rating = int(param)
            _record_satisfaction_rating(phone, rating)
        except ValueError:
            pass

    # PRD NPS responses
    elif action == 'nps' and param:
        _handle_nps_response(phone, param)

    else:
        logger.info(f"Acao de lista nao reconhecida: {row_id}")


def _handle_text_message(phone, text):
    """
    Processa mensagem de texto recebida.
    Chatbot simples com comandos.
    """
    text = text.strip().lower()
    logger.info(f"Mensagem recebida de {phone}: {text}")

    from app.services.megaapi import megaapi, Button

    user = User.query.filter_by(phone=phone).first()
    user_id = user.id if user else None

    if text in ('oi', 'ola', 'hey', 'bom dia', 'boa tarde', 'boa noite'):
        _send_welcome_menu(phone, user)

    elif text in ('horarios', 'horario', 'agendar', 'agendar aula'):
        _send_available_slots(phone)

    elif text in ('meu treino', 'treino', 'ficha'):
        megaapi.send_custom_message(
            phone=phone,
            message="Acesse seu treino personalizado em:\n"
                    "/student/my-training\n\n"
                    "La voce encontra todos os exercicios do dia com videos!",
            user_id=user_id
        )

    elif text in ('ajuda', 'help', 'menu'):
        _send_welcome_menu(phone, user)

    elif text in ('creditos', 'credito', 'saldo'):
        if user:
            megaapi.send_custom_message(
                phone=phone,
                message=f"Ola {user.name.split()[0]}! "
                        f"Seu saldo atual e de {getattr(user, 'credits', 0)} creditos.",
                user_id=user_id
            )
        else:
            megaapi.send_custom_message(
                phone=phone,
                message="Nao encontrei seu cadastro. "
                        "Por favor, entre em contato com a recepcao.",
                user_id=user_id
            )

    else:
        logger.info(f"Mensagem nao processada de {phone}: {text[:50]}")


# ============================================================
# ACOES ESPECIFICAS
# ============================================================

def _confirm_booking_attendance(booking_id, phone):
    """Confirma presenca em aula via WhatsApp."""
    from app.services.megaapi import megaapi

    booking = Booking.query.get(booking_id)

    if not booking:
        logger.error(f"Booking {booking_id} nao encontrado")
        return

    if booking.user.phone != phone:
        logger.warning(f"Tentativa de confirmar booking de outro usuario")
        return

    try:
        megaapi.send_custom_message(
            phone=phone,
            message=f"Presenca confirmada! Te esperamos as {booking.schedule.start_time.strftime('%H:%M')}.",
            user_id=booking.user_id
        )
    except Exception as e:
        logger.error(f"Erro ao enviar confirmacao: {e}")

    logger.info(f"Booking {booking_id} confirmado por {phone}")


def _cancel_booking_via_whatsapp(booking_id, phone):
    """Cancela booking via WhatsApp."""
    from app.services.megaapi import megaapi

    booking = Booking.query.get(booking_id)

    if not booking or booking.user.phone != phone:
        return

    if hasattr(booking, 'can_cancel') and not booking.can_cancel:
        megaapi.send_custom_message(
            phone=phone,
            message="Nao e possivel cancelar com menos de 2 horas de antecedencia. "
                    "Entre em contato conosco.",
            user_id=booking.user_id
        )
        return

    try:
        booking.cancel(reason="Cancelado via WhatsApp")
        logger.info(f"Booking {booking_id} cancelado via WhatsApp")

        megaapi.send_custom_message(
            phone=phone,
            message="Aula cancelada com sucesso! Seu credito foi estornado.",
            user_id=booking.user_id
        )
    except Exception as e:
        logger.error(f"Erro ao cancelar booking {booking_id}: {e}")


def _send_available_slots(phone):
    """Envia lista de horarios disponiveis para reagendamento."""
    from app.services.megaapi import megaapi
    from app.models import ClassSchedule
    from datetime import timedelta

    user = User.query.filter_by(phone=phone).first()
    if not user:
        return

    # Buscar aulas disponiveis
    schedules = ClassSchedule.query.filter(
        ClassSchedule.is_active == True
    ).order_by(ClassSchedule.start_time).all()

    if not schedules:
        megaapi.send_custom_message(
            phone=phone,
            message="Nao ha horarios disponiveis no momento. "
                    "Entre em contato com a recepcao.",
            user_id=user.id
        )
        return

    # Montar lista interativa
    sections = []
    rows = []
    for schedule in schedules[:10]:
        modality_name = schedule.modality.name if schedule.modality else 'Aula'
        time_str = schedule.start_time.strftime('%H:%M') if schedule.start_time else '00:00'
        rows.append({
            "title": f"{time_str} - {modality_name}",
            "rowId": f"slot_{schedule.id}",
            "description": f"com {schedule.instructor.name if schedule.instructor else 'Instrutor'}"
        })

    if rows:
        sections.append({
            "title": "Horarios Disponiveis",
            "rows": rows
        })

        megaapi.send_list_message(
            phone=phone,
            text="Escolha um horario para sua aula:",
            button_text="Ver Horarios",
            sections=sections,
            user_id=user.id
        )


def _book_slot_via_whatsapp(schedule_id, phone):
    """Reserva aula via WhatsApp."""
    from app.services.megaapi import megaapi
    from app.models import ClassSchedule

    user = User.query.filter_by(phone=phone).first()
    if not user:
        return

    schedule = ClassSchedule.query.get(schedule_id)
    if not schedule:
        megaapi.send_custom_message(
            phone=phone,
            message="Horario nao encontrado. Tente novamente.",
            user_id=user.id
        )
        return

    try:
        # Criar booking
        today = datetime.now().date()
        new_booking = Booking(
            user_id=user.id,
            schedule_id=schedule.id,
            date=today,
            status=BookingStatus.CONFIRMED
        )
        db.session.add(new_booking)
        db.session.commit()

        modality_name = schedule.modality.name if schedule.modality else 'Aula'
        time_str = schedule.start_time.strftime('%H:%M') if schedule.start_time else ''

        megaapi.send_custom_message(
            phone=phone,
            message=f"Aula agendada com sucesso!\n\n"
                    f"Modalidade: {modality_name}\n"
                    f"Horario: {time_str}\n"
                    f"Data: {today.strftime('%d/%m/%Y')}\n\n"
                    f"Te esperamos!",
            user_id=user.id
        )
        logger.info(f"Booking criado via WhatsApp: user={user.id} schedule={schedule_id}")

    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao criar booking via WhatsApp: {e}")
        megaapi.send_custom_message(
            phone=phone,
            message="Nao foi possivel agendar. Tente novamente ou entre em contato com a recepcao.",
            user_id=user.id
        )


def _send_welcome_menu(phone, user=None):
    """Envia menu de boas-vindas com botoes."""
    from app.services.megaapi import megaapi, Button

    first_name = user.name.split()[0] if user and user.name else 'voce'
    user_id = user.id if user else None

    buttons = [
        Button(id='schedule_now', title='Agendar Aula'),
        Button(id='view_training', title='Meu Treino'),
        Button(id='schedule_call', title='Falar Conosco')
    ]

    megaapi.send_buttons(
        phone=phone,
        message=f"Ola {first_name}! Seja bem-vindo(a) a nossa academia!\n\n"
                f"Como posso ajudar?",
        buttons=buttons,
        user_id=user_id
    )


def _record_satisfaction_rating(phone, rating):
    """Registra avaliacao de satisfacao."""
    from app.services.megaapi import megaapi

    user = User.query.filter_by(phone=phone).first()
    if not user:
        return

    # Registrar no log de automacao
    log = AutomationLog(
        user_id=user.id,
        automation_type=f'SATISFACTION_RATING_{rating}',
        sent_at=datetime.utcnow()
    )
    db.session.add(log)
    db.session.commit()

    if rating >= 4:
        megaapi.send_custom_message(
            phone=phone,
            message="Obrigado pela avaliacao! Ficamos felizes que esta gostando!",
            user_id=user.id
        )
    elif rating == 3:
        megaapi.send_custom_message(
            phone=phone,
            message="Obrigado pelo feedback! Vamos trabalhar para melhorar sua experiencia.",
            user_id=user.id
        )
    else:
        megaapi.send_custom_message(
            phone=phone,
            message="Lamentamos que sua experiencia nao esteja sendo boa. "
                    "Um membro da equipe vai entrar em contato para entender melhor.",
            user_id=user.id
        )
        logger.warning(f"Avaliacao baixa ({rating}) de {user.name} (ID: {user.id})")

    logger.info(f"Satisfacao registrada: user={user.id} rating={rating}")


def _handle_nps_response(phone, nps_value):
    """PRD: Processa resposta NPS. Ruim aciona alerta para gerente."""
    from app.services.megaapi import megaapi

    user = User.query.filter_by(phone=phone).first()
    if not user:
        return

    # Registrar NPS
    log = AutomationLog(
        user_id=user.id,
        automation_type=f'NPS_RESPONSE_{nps_value.upper()}',
        sent_at=datetime.utcnow()
    )
    db.session.add(log)
    db.session.commit()

    nps_map = {
        'excelente': ('Obrigado! Ficamos muito felizes que está adorando!', False),
        'boa': ('Obrigado pelo feedback positivo! Vamos continuar melhorando.', False),
        'regular': ('Agradecemos o feedback! Vamos trabalhar para melhorar sua experiência.', True),
        'ruim': ('Lamentamos muito. Um gerente vai entrar em contato em até 24h para entender melhor.', True),
    }

    response_msg, alert_manager = nps_map.get(nps_value, ('Obrigado pelo feedback!', False))

    megaapi.send_custom_message(
        phone=phone,
        message=response_msg,
        user_id=user.id
    )

    # PRD: Ruim aciona alerta para gerente
    if alert_manager:
        try:
            manager = User.query.filter(
                User.role.in_(['admin', 'manager']),
                User.is_active == True,
                User.phone.isnot(None)
            ).first()

            if manager:
                megaapi.send_custom_message(
                    phone=manager.phone,
                    message=(f"⚠️ *Alerta NPS*\n\n"
                             f"Aluno: {user.name}\n"
                             f"Avaliação: {nps_value.upper()}\n"
                             f"Telefone: {user.phone}\n\n"
                             f"Recomendação: agendar ligação em até 24h."),
                    user_id=manager.id
                )
                logger.warning(f"NPS {nps_value} de {user.name} - alerta enviado ao gerente")
        except Exception as e:
            logger.error(f"Erro ao alertar gerente sobre NPS: {e}")

    logger.info(f"NPS registrado: user={user.id} valor={nps_value}")


def _log_button_interaction(user_id, button_id):
    """Registra interacao com botao no AutomationLog."""
    try:
        log = AutomationLog(
            user_id=user_id,
            automation_type=f'BUTTON_CLICK_{button_id}',
            sent_at=datetime.utcnow(),
            clicked=True
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao logar interacao de botao: {e}")


# ============================================================
# HEALTH CHECK
# ============================================================

@webhooks_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint para monitoramento."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    }), 200
