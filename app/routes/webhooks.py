# app/routes/webhooks.py

from flask import Blueprint, request, jsonify
from app.models import WhatsAppLog
from app import db
from datetime import datetime

webhooks_bp = Blueprint('webhooks', __name__, url_prefix='/webhooks')


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
