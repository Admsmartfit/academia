# app/routes/webhooks.py

from flask import Blueprint, request, jsonify, current_app
from app.models import WhatsAppLog, Payment
from app.models.payment import PaymentStatusEnum
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

def validate_nupay_signature(request):
    """
    Valida HMAC-SHA256 do webhook NuPay.

    A NuPay envia o header X-NuPay-Signature com a assinatura
    calculada usando o webhook secret configurado.

    Returns:
        bool: True se válido, False se inválido
    """
    signature = request.headers.get('X-NuPay-Signature')

    if not signature:
        logger.warning("Webhook NuPay recebido sem assinatura")
        return False

    secret = current_app.config.get('NUPAY_WEBHOOK_SECRET', '')

    if not secret:
        # Em modo desenvolvimento, aceita sem secret configurado
        logger.warning("NUPAY_WEBHOOK_SECRET não configurado - aceitando webhook sem validação")
        return True

    payload = request.get_data()

    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    is_valid = hmac.compare_digest(signature, expected)

    if not is_valid:
        logger.warning(f"Assinatura NuPay inválida. Recebida: {signature[:20]}...")

    return is_valid


@webhooks_bp.route('/nupay/callback', methods=['POST'])
def nupay_callback():
    """
    Recebe callbacks da NuPay sobre status de pagamentos.

    Eventos esperados:
    - COMPLETED: Pagamento confirmado
    - FAILED: Pagamento falhou
    - CANCELLED: Pagamento cancelado
    - EXPIRED: PIX expirou

    Payload esperado:
    {
        "pspReferenceId": "NUPAY_123456789",
        "merchantReferenceId": "PAYMENT_42",
        "status": "COMPLETED",
        "amount": {"value": 199.00, "currency": "BRL"},
        "paymentMethod": {"type": "nupay"},
        "timestamp": "2026-01-23T14:30:00Z"
    }
    """
    try:
        # 1. Validar assinatura
        if not validate_nupay_signature(request):
            logger.error("Webhook NuPay: assinatura inválida")
            return jsonify({"error": "Invalid signature"}), 401

        data = request.get_json()

        if not data:
            logger.error("Webhook NuPay: payload vazio")
            return jsonify({"error": "No data received"}), 400

        # 2. Extrair dados do payload
        merchant_reference = data.get('merchantReferenceId', '')
        psp_reference = data.get('pspReferenceId', '')
        status = data.get('status', '')

        logger.info(f"Webhook NuPay recebido: {merchant_reference} - Status: {status}")

        # 3. Buscar payment pelo reference (formato: PAYMENT_42)
        payment = Payment.query.filter_by(nupay_reference_id=merchant_reference).first()

        if not payment:
            # Tentar buscar pelo ID extraído do reference
            try:
                if merchant_reference.startswith('PAYMENT_'):
                    payment_id = int(merchant_reference.replace('PAYMENT_', ''))
                    payment = Payment.query.get(payment_id)
            except (ValueError, TypeError):
                pass

        if not payment:
            logger.warning(f"Webhook NuPay: Payment não encontrado para {merchant_reference}")
            return jsonify({"error": "Payment not found"}), 404

        # 4. Atualizar pspReferenceId se ainda não tiver
        if psp_reference and not payment.nupay_psp_reference_id:
            payment.nupay_psp_reference_id = psp_reference

        # 5. Processar conforme status
        if status == 'COMPLETED':
            _process_payment_completed(payment, data)

        elif status == 'FAILED':
            _process_payment_failed(payment, data)

        elif status == 'CANCELLED':
            payment.status = PaymentStatusEnum.CANCELLED
            logger.info(f"Payment #{payment.id} marcado como cancelado")

        elif status == 'EXPIRED':
            # PIX expirou, manter como PENDING para nova tentativa
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
    """
    Processa pagamento confirmado.

    - Marca payment como pago
    - Desbloqueia subscription se necessário
    - Aplica bônus XP de boas-vindas
    - Envia notificação WhatsApp
    """
    # Marcar como pago
    payment.mark_as_paid()
    logger.info(f"Payment #{payment.id} marcado como PAID")

    subscription = payment.subscription
    user = subscription.user
    package = subscription.package

    # Desbloquear subscription se estava bloqueada
    if subscription.is_blocked:
        subscription.unblock()
        logger.info(f"Subscription #{subscription.id} desbloqueada")

    # Aplicar bônus XP de boas-vindas (apenas na primeira parcela)
    if payment.installment_number == 1:
        xp_bonus = package.welcome_xp_bonus or 0
        if xp_bonus > 0:
            user.add_xp(xp_bonus)
            logger.info(f"User #{user.id} recebeu {xp_bonus} XP de boas-vindas")

    # Enviar notificação WhatsApp
    try:
        from app.services.megaapi import megaapi

        first_name = user.name.split()[0] if user.name else 'Cliente'

        megaapi.send_custom_message(
            phone=user.phone,
            message=f"✅ Olá {first_name}! Seu pagamento foi confirmado. "
                    f"Você tem {subscription.credits_remaining} créditos disponíveis "
                    f"até {subscription.end_date.strftime('%d/%m/%Y')}. Bora treinar! 💪",
            user_id=user.id
        )
        logger.info(f"WhatsApp de confirmação enviado para {user.phone}")

    except Exception as e:
        # Não falhar o webhook por erro de WhatsApp
        logger.error(f"Erro ao enviar WhatsApp de confirmação: {str(e)}")


def _process_payment_failed(payment, data):
    """
    Processa pagamento que falhou.

    - Atualiza status do payment
    - Envia notificação WhatsApp
    """
    payment.status = PaymentStatusEnum.PENDING  # Volta para pending para nova tentativa
    logger.info(f"Payment #{payment.id} marcado como falha - voltou para PENDING")

    # Enviar notificação WhatsApp
    try:
        from app.services.megaapi import megaapi

        user = payment.subscription.user
        first_name = user.name.split()[0] if user.name else 'Cliente'

        megaapi.send_custom_message(
            phone=user.phone,
            message=f"❌ Olá {first_name}, houve um problema com seu pagamento. "
                    f"Por favor, tente novamente ou entre em contato conosco.",
            user_id=user.id
        )
        logger.info(f"WhatsApp de falha enviado para {user.phone}")

    except Exception as e:
        logger.error(f"Erro ao enviar WhatsApp de falha: {str(e)}")


@webhooks_bp.route('/nupay/subscription', methods=['POST'])
def nupay_subscription_callback():
    """
    Recebe callbacks da NuPay sobre assinaturas recorrentes.

    Eventos:
    - SUBSCRIPTION_RENEWED: Cobrança recorrente realizada
    - SUBSCRIPTION_CANCELLED: Assinatura cancelada
    - SUBSCRIPTION_PAUSED: Assinatura pausada
    """
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
            logger.warning(f"Subscription não encontrada: {subscription_id}")
            return jsonify({"error": "Subscription not found"}), 404

        if event == 'SUBSCRIPTION_RENEWED':
            # Criar novo payment e renovar créditos
            _process_subscription_renewed(subscription, data)

        elif event == 'SUBSCRIPTION_CANCELLED':
            subscription.recurring_status = 'CANCELLED'
            subscription.is_recurring = False
            logger.info(f"Subscription #{subscription.id} recorrência cancelada")

        elif event == 'SUBSCRIPTION_PAUSED':
            subscription.recurring_status = 'PAUSED'
            logger.info(f"Subscription #{subscription.id} recorrência pausada")

        db.session.commit()

        return jsonify({"status": "ok"}), 200

    except Exception as e:
        logger.error(f"Erro no webhook NuPay Subscription: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


def _process_subscription_renewed(subscription, data):
    """
    Processa renovação de assinatura recorrente.

    - Cria novo Payment
    - Renova créditos
    - Atualiza datas de billing
    - Notifica usuário
    """
    from datetime import date, timedelta

    package = subscription.package
    user = subscription.user

    # Criar novo Payment para esta cobrança
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

    # Renovar créditos
    subscription.credits_total += package.credits
    subscription.last_billing_date = date.today()
    subscription.next_billing_date = date.today() + timedelta(
        days=package.recurring_interval_days or 30
    )

    # Estender validade
    subscription.end_date = date.today() + timedelta(days=package.validity_days)

    logger.info(f"Subscription #{subscription.id} renovada: +{package.credits} créditos")

    # Notificar usuário
    try:
        from app.services.megaapi import megaapi

        first_name = user.name.split()[0] if user.name else 'Cliente'

        megaapi.send_custom_message(
            phone=user.phone,
            message=f"🔄 Olá {first_name}! Sua assinatura foi renovada automaticamente. "
                    f"+{package.credits} créditos adicionados! "
                    f"Total disponível: {subscription.credits_remaining} créditos. 💪",
            user_id=user.id
        )
    except Exception as e:
        logger.error(f"Erro ao enviar WhatsApp de renovação: {str(e)}")


@webhooks_bp.route('/megaapi', methods=['POST'])
def megaapi_webhook():
    """
    Recebe callbacks da Megaapi sobre status de mensagens

    Eventos:
    - message_sent: Mensagem enviada
    - message_delivered: Mensagem entregue
    - message_read: Mensagem lida
    - message_failed: Falha no envio
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data received'}), 400

        event_type = data.get('event')
        message_id = data.get('message_id')

        if not message_id:
            return jsonify({'error': 'No message_id'}), 400

        # Buscar log da mensagem
        log = WhatsAppLog.query.filter_by(message_id=message_id).first()

        if not log:
            # Log nao encontrado, criar novo
            log = WhatsAppLog(
                message_id=message_id,
                phone=data.get('phone', ''),
                template_name=data.get('template_name', 'unknown'),
                status='pending'
            )
            db.session.add(log)

        # Atualizar status baseado no evento
        if event_type == 'message_sent':
            log.status = 'sent'
        elif event_type == 'message_delivered':
            log.status = 'delivered'
            log.delivered_at = datetime.utcnow()
        elif event_type == 'message_read':
            log.status = 'read'
            log.read_at = datetime.utcnow()
        elif event_type == 'message_failed':
            log.status = 'failed'
            log.error_message = data.get('error', 'Unknown error')

        # Armazenar dados adicionais
        log.response_json = data

        db.session.commit()

        return jsonify({'status': 'ok'}), 200

    except Exception as e:
        print(f"Erro no webhook Megaapi: {e}")
        return jsonify({'error': str(e)}), 500


@webhooks_bp.route('/megaapi/incoming', methods=['POST'])
def megaapi_incoming():
    """
    Recebe mensagens de entrada (respostas dos clientes)
    Inclui processamento de List Messages (botoes interativos)
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data received'}), 400

        phone = data.get('from')
        message = data.get('message', {})
        message_text = message.get('text', '')

        # Verificar se e resposta de lista (List Message)
        if 'listResponseMessage' in message:
            response = message['listResponseMessage']
            row_id = response.get('singleSelectReply', {}).get('selectedRowId')

            if row_id:
                try:
                    # Parsear "confirm_123" ou "cancel_123"
                    parts = row_id.split('_')
                    if len(parts) >= 2:
                        action = parts[0]
                        booking_id = int(parts[1])

                        from app.models import Booking, BookingStatus
                        from app.services.megaapi import megaapi

                        booking = Booking.query.get(booking_id)

                        if booking:
                            if action == 'cancel':
                                if booking.can_cancel:
                                    booking.cancel(reason="Cancelado via WhatsApp")
                                    print(f"[WEBHOOK] Booking {booking_id} cancelado via WhatsApp")

                                    # Enviar confirmacao
                                    try:
                                        megaapi.send_custom_message(
                                            phone=booking.user.phone,
                                            message="Aula cancelada com sucesso! Seu credito foi estornado.",
                                            user_id=booking.user_id
                                        )
                                    except Exception as msg_error:
                                        print(f"[WEBHOOK] Erro ao enviar confirmacao: {msg_error}")
                                else:
                                    # Nao pode cancelar (menos de 2h)
                                    try:
                                        megaapi.send_custom_message(
                                            phone=booking.user.phone,
                                            message="Nao e possivel cancelar com menos de 2 horas de antecedencia.",
                                            user_id=booking.user_id
                                        )
                                    except Exception as msg_error:
                                        print(f"[WEBHOOK] Erro ao enviar aviso: {msg_error}")

                            elif action == 'confirm':
                                print(f"[WEBHOOK] Booking {booking_id} confirmado via WhatsApp")

                                # Enviar confirmacao
                                try:
                                    megaapi.send_custom_message(
                                        phone=booking.user.phone,
                                        message=f"Presenca confirmada! Te esperamos as {booking.schedule.start_time.strftime('%H:%M')}.",
                                        user_id=booking.user_id
                                    )
                                except Exception as msg_error:
                                    print(f"[WEBHOOK] Erro ao enviar confirmacao: {msg_error}")
                        else:
                            print(f"[WEBHOOK] Booking {booking_id} nao encontrado")

                except (ValueError, IndexError) as parse_error:
                    print(f"[WEBHOOK] Erro ao parsear row_id '{row_id}': {parse_error}")

        else:
            # Mensagem de texto normal
            print(f"[WEBHOOK] Mensagem recebida de {phone}: {message_text[:50]}...")

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
        print(f"Erro no webhook incoming: {e}")
        return jsonify({'error': str(e)}), 500


@webhooks_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint para monitoramento
    """
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    }), 200
