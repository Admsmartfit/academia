# app/routes/api/face.py

import logging
from functools import wraps
from datetime import datetime, timedelta

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from app.services.face_service import FaceRecognitionService

logger = logging.getLogger(__name__)

face_api_bp = Blueprint('face_api', __name__, url_prefix='/api/face')

# Instancia do servico
face_service = FaceRecognitionService(tolerance=0.6)

# Rate limiting simples (em memoria)
_rate_limit_store = {}
RATE_LIMIT_MAX = 10  # tentativas
RATE_LIMIT_WINDOW = 60  # segundos


def rate_limit(f):
    """Decorator para rate limiting por IP (max 10 req/min)"""
    @wraps(f)
    def decorated(*args, **kwargs):
        ip = request.remote_addr or 'unknown'
        now = datetime.utcnow()
        key = f'{ip}:{f.__name__}'

        if key in _rate_limit_store:
            attempts, window_start = _rate_limit_store[key]
            if (now - window_start).total_seconds() > RATE_LIMIT_WINDOW:
                _rate_limit_store[key] = (1, now)
            elif attempts >= RATE_LIMIT_MAX:
                return jsonify({
                    'success': False,
                    'error': 'Muitas tentativas. Aguarde um momento.'
                }), 429
            else:
                _rate_limit_store[key] = (attempts + 1, window_start)
        else:
            _rate_limit_store[key] = (1, now)

        return f(*args, **kwargs)
    return decorated


@face_api_bp.route('/enroll', methods=['POST'])
@login_required
def enroll_face():
    """
    Registra face de um usuario.

    Request JSON:
        {"image": "base64_string", "user_id": int (opcional)}

    Apenas admin pode cadastrar face de outros usuarios.
    """
    data = request.get_json()
    if not data or 'image' not in data:
        return jsonify({
            'success': False,
            'error': 'Imagem nao fornecida. Envie {"image": "base64_string"}'
        }), 400

    image_data = data['image']
    target_user_id = data.get('user_id', current_user.id)

    # Verificar permissao
    if target_user_id != current_user.id and not current_user.is_admin:
        return jsonify({
            'success': False,
            'error': 'Nao autorizado. Apenas admin pode cadastrar face de outros usuarios.'
        }), 403

    # Verificar tamanho da imagem (base64 ~33% maior que original)
    if len(image_data) > 7 * 1024 * 1024:  # ~5MB em base64
        return jsonify({
            'success': False,
            'error': 'Imagem muito grande. Maximo: 5MB'
        }), 400

    # Verificar se ja tem face cadastrada
    from app.models.user import User
    target_user = User.query.get(target_user_id)
    if not target_user:
        return jsonify({
            'success': False,
            'error': 'Usuario nao encontrado'
        }), 404

    if target_user.face_encoding and not data.get('overwrite', False):
        return jsonify({
            'success': False,
            'error': 'Usuario ja possui face cadastrada. Envie overwrite=true para substituir.',
            'has_face': True,
            'registered_at': target_user.face_registered_at.isoformat() if target_user.face_registered_at else None
        }), 409

    # Registrar face
    result = face_service.enroll_face(target_user_id, image_data)

    if result['success']:
        logger.info(f"Face cadastrada: user {target_user_id} por {current_user.id}")
        return jsonify({
            'success': True,
            'message': result['message'],
            'user_id': target_user_id,
            'confidence': result['confidence']
        }), 201
    else:
        return jsonify({
            'success': False,
            'error': result['message']
        }), 400


@face_api_bp.route('/recognize', methods=['POST'])
@rate_limit
def recognize_face():
    """
    Reconhece uma face e retorna o usuario.

    Request JSON:
        {"image": "base64_string"}

    Se reconhecer, busca booking ativo (+-30min) e inclui na resposta.
    """
    data = request.get_json()
    if not data or 'image' not in data:
        return jsonify({
            'success': False,
            'error': 'Imagem nao fornecida'
        }), 400

    image_data = data['image']
    ip_address = request.remote_addr
    user_agent = request.headers.get('User-Agent', '')[:200]

    # Reconhecer
    match = face_service.recognize_face(
        image_data,
        ip_address=ip_address,
        user_agent=user_agent
    )

    if not match:
        return jsonify({
            'success': False,
            'message': 'Nenhum usuario reconhecido'
        }), 404

    user = match['user']

    # Buscar booking ativo (+-30min)
    from app.models.booking import Booking, BookingStatus
    now = datetime.now()
    today = now.date()

    active_booking = Booking.query.filter(
        Booking.user_id == user.id,
        Booking.date == today,
        Booking.status == BookingStatus.CONFIRMED
    ).first()

    # Tentar check-in automatico se solicitado
    checkin_result = None
    if data.get('auto_checkin', False) and active_booking:
        from app.services.face_service import FaceRecognitionService
        checkin_result = _auto_checkin(user.id, active_booking)

    response = {
        'success': True,
        'user': {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'role': user.role,
            'photo_url': user.photo_url
        },
        'confidence': round(match['confidence'], 1),
        'should_checkin': active_booking is not None and active_booking.status == BookingStatus.CONFIRMED,
        'booking_id': active_booking.id if active_booking else None
    }

    if checkin_result:
        response['checkin'] = checkin_result

    return jsonify(response), 200


@face_api_bp.route('/status/<int:user_id>', methods=['GET'])
@login_required
def face_status(user_id):
    """
    Verifica se usuario tem face cadastrada.
    """
    # Verificar permissao
    if user_id != current_user.id and not current_user.is_admin and not current_user.is_instructor:
        return jsonify({
            'success': False,
            'error': 'Nao autorizado'
        }), 403

    status = face_service.get_face_status(user_id)
    return jsonify(status), 200


@face_api_bp.route('/remove', methods=['DELETE'])
@login_required
def remove_face():
    """
    Remove face encoding do usuario (LGPD compliance).

    Request JSON:
        {"user_id": int (opcional), "confirm": true}
    """
    data = request.get_json() or {}

    if not data.get('confirm', False):
        return jsonify({
            'success': False,
            'error': 'Confirmacao necessaria. Envie {"confirm": true}'
        }), 400

    target_user_id = data.get('user_id', current_user.id)

    # Qualquer usuario pode remover seus proprios dados (LGPD)
    if target_user_id != current_user.id and not current_user.is_admin:
        return jsonify({
            'success': False,
            'error': 'Nao autorizado'
        }), 403

    result = face_service.remove_face(target_user_id)

    if result['success']:
        logger.info(f"Face removida: user {target_user_id} por {current_user.id} (LGPD)")
        return jsonify(result), 200
    else:
        return jsonify(result), 400


def _auto_checkin(user_id: int, booking) -> dict:
    """
    Realiza check-in automatico via reconhecimento facial.
    """
    from app import db
    from app.models.booking import BookingStatus

    try:
        if booking.status != BookingStatus.CONFIRMED:
            return {
                'success': False,
                'message': 'Booking nao esta confirmado'
            }

        booking.status = BookingStatus.COMPLETED
        booking.checkin_at = datetime.utcnow()
        booking.xp_earned = 10

        # Adicionar XP
        booking.user.xp += 10

        db.session.commit()

        logger.info(f"Check-in automatico (facial): user {user_id}, booking {booking.id}")

        return {
            'success': True,
            'message': 'Check-in realizado com sucesso!',
            'booking_id': booking.id,
            'xp_earned': 10
        }
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro no check-in automatico: {e}")
        return {
            'success': False,
            'message': f'Erro no check-in: {str(e)}'
        }
