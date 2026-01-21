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
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data received'}), 400

        phone = data.get('from')
        message = data.get('message', {})
        message_text = message.get('text', '')

        # Aqui pode implementar logica para processar respostas
        # Por exemplo: confirmacoes, cancelamentos por mensagem, etc.

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
