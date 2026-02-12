from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from sqlalchemy import func
from app.models import User, StudentHealthScore, Booking, AutomationLog, SystemConfig
from app import db

crm_api_bp = Blueprint('crm_api', __name__, url_prefix='/api/crm')


@crm_api_bp.route('/dashboard/summary')
@login_required
def dashboard_summary():
    """Retorna resumo de KPIs"""
    if not current_user.is_admin and current_user.role != 'manager':
        return jsonify({'error': 'Unauthorized'}), 403

    total_students = User.query.filter_by(role='student', is_active=True).count()

    # Buscar ultimo score de cada aluno
    subquery = db.session.query(
        StudentHealthScore.user_id,
        func.max(StudentHealthScore.calculated_at).label('max_date')
    ).group_by(StudentHealthScore.user_id).subquery()

    recent_scores = db.session.query(StudentHealthScore).join(
        subquery,
        (StudentHealthScore.user_id == subquery.c.user_id) &
        (StudentHealthScore.calculated_at == subquery.c.max_date)
    ).all()

    at_risk = sum(1 for s in recent_scores if s.risk_level.name in ['HIGH', 'CRITICAL'])
    critical = sum(1 for s in recent_scores if s.risk_level.name == 'CRITICAL')

    avg_score = 0
    if recent_scores:
        avg_score = sum(s.total_score for s in recent_scores) / len(recent_scores)

    return jsonify({
        'total_students': total_students,
        'at_risk': at_risk,
        'critical': critical,
        'avg_score': round(avg_score, 1)
    })


@crm_api_bp.route('/students/at-risk')
@login_required
def students_at_risk():
    """Retorna alunos em risco com detalhes"""
    if not current_user.is_admin and current_user.role != 'manager':
        return jsonify({'error': 'Unauthorized'}), 403

    # Buscar ultimo score de cada aluno
    subquery = db.session.query(
        StudentHealthScore.user_id,
        func.max(StudentHealthScore.calculated_at).label('max_date')
    ).group_by(StudentHealthScore.user_id).subquery()

    scores = db.session.query(StudentHealthScore).join(
        subquery,
        (StudentHealthScore.user_id == subquery.c.user_id) &
        (StudentHealthScore.calculated_at == subquery.c.max_date)
    ).join(User).order_by(StudentHealthScore.total_score).limit(100).all()

    cutoff_30d = datetime.utcnow() - timedelta(days=30)
    data = []

    for score in scores:
        user = score.user

        # Ultimo checkin
        last_checkin = Booking.query.filter(
            Booking.user_id == user.id,
            Booking.status == 'COMPLETED'
        ).order_by(Booking.checked_in_at.desc()).first()

        last_checkin_date = None
        days_since = -1
        if last_checkin and last_checkin.checked_in_at:
            last_checkin_date = last_checkin.checked_in_at.isoformat()
            days_since = (datetime.utcnow() - last_checkin.checked_in_at).days

        # Frequencia real nos ultimos 30 dias
        freq_30d = Booking.query.filter(
            Booking.user_id == user.id,
            Booking.status == 'COMPLETED',
            Booking.checked_in_at >= cutoff_30d
        ).count()

        data.append({
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'phone': getattr(user, 'phone', None),
            'avatar_url': getattr(user, 'photo_url', None),
            'health_score': score.total_score,
            'risk_level': score.risk_level.name,
            'last_checkin': last_checkin_date,
            'days_since_checkin': days_since,
            'frequency_30d': freq_30d
        })

    return jsonify(data)


@crm_api_bp.route('/send-message', methods=['POST'])
@login_required
def send_message():
    """Envia mensagem de recuperacao via WhatsApp"""
    if not current_user.is_admin and current_user.role != 'manager':
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.json
    student_id = data.get('student_id')
    message_type = data.get('message_type', 'RECOVERY')

    if not student_id:
        return jsonify({'success': False, 'error': 'student_id obrigatorio'}), 400

    student = User.query.get(student_id)
    if not student or not student.phone:
        return jsonify({'success': False, 'error': 'Aluno nao encontrado ou sem telefone'}), 404

    try:
        from app.services.megaapi import megaapi, Button

        first_name = student.name.split()[0] if student.name else 'Aluno'

        if message_type == 'RECOVERY':
            buttons = [
                Button(id='yes_tomorrow', title='Vou amanha!'),
                Button(id='reschedule_me', title='Reagendar'),
                Button(id='im_ok', title='Esta tudo bem')
            ]
            msg = (f"Ola {first_name}!\n\n"
                   f"Sentimos sua falta por aqui! Sabemos que a rotina e corrida, "
                   f"mas cada treino te deixa mais perto dos seus objetivos!\n\n"
                   f"Quando podemos te esperar?")
            megaapi.send_buttons(phone=student.phone, message=msg, buttons=buttons, user_id=student.id)

        elif message_type == 'DISCOUNT':
            buttons = [
                Button(id='claim_discount', title='Quero o desconto'),
                Button(id='schedule_call', title='Agendar ligacao')
            ]
            msg = (f"{first_name}, preparamos uma condicao ESPECIAL so para voce:\n\n"
                   f"30% DE DESCONTO no proximo mes\n"
                   f"1 sessao de personal trainer gratis\n\n"
                   f"Sua saude e nossa prioridade!")
            megaapi.send_buttons(phone=student.phone, message=msg, buttons=buttons, user_id=student.id)

        elif message_type == 'CALL':
            msg = (f"Ola {first_name}! Vamos agendar uma ligacao para conversar sobre "
                   f"como podemos te ajudar a voltar a treinar. "
                   f"Nossa equipe vai entrar em contato em breve!")
            megaapi.send_custom_message(phone=student.phone, message=msg, user_id=student.id)

        else:
            msg = (f"Ola {first_name}! Estamos com saudade de voce na academia. "
                   f"Que tal voltar a treinar? Conte conosco!")
            megaapi.send_custom_message(phone=student.phone, message=msg, user_id=student.id)

        # Registrar log de automacao manual
        log = AutomationLog(
            user_id=student.id,
            automation_type=f'MANUAL_{message_type}',
            sent_at=datetime.utcnow()
        )
        db.session.add(log)

        # Atualizar health score com acao tomada
        latest_score = StudentHealthScore.query.filter_by(
            user_id=student.id
        ).order_by(StudentHealthScore.calculated_at.desc()).first()
        if latest_score:
            latest_score.last_action_taken = f'{message_type} por {current_user.name}'
            latest_score.last_action_at = datetime.utcnow()

        db.session.commit()

        return jsonify({'success': True, 'message': f'Mensagem {message_type} enviada para {first_name}'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@crm_api_bp.route('/student/<int:student_id>/history')
@login_required
def student_history(student_id):
    """Retorna historico de health scores de um aluno"""
    if not current_user.is_admin and current_user.role != 'manager':
        return jsonify({'error': 'Unauthorized'}), 403

    scores = StudentHealthScore.query.filter_by(
        user_id=student_id
    ).order_by(StudentHealthScore.calculated_at.desc()).limit(30).all()

    automations = AutomationLog.query.filter_by(
        user_id=student_id
    ).order_by(AutomationLog.sent_at.desc()).limit(20).all()

    return jsonify({
        'scores': [{
            'date': s.calculated_at.isoformat(),
            'total_score': s.total_score,
            'frequency_score': s.frequency_score,
            'engagement_score': s.engagement_score,
            'financial_score': s.financial_score,
            'tenure_score': s.tenure_score,
            'risk_level': s.risk_level.name
        } for s in scores],
        'automations': [{
            'type': a.automation_type,
            'sent_at': a.sent_at.isoformat(),
            'opened': a.opened,
            'clicked': a.clicked
        } for a in automations]
    })


@crm_api_bp.route('/nps/average')
@login_required
def nps_average():
    """Retorna a media NPS baseada nos logs de automacao NPS"""
    if not current_user.is_admin and current_user.role != 'manager':
        return jsonify({'error': 'Unauthorized'}), 403

    # Buscar respostas NPS dos ultimos 90 dias
    cutoff = datetime.utcnow() - timedelta(days=90)
    nps_logs = AutomationLog.query.filter(
        AutomationLog.automation_type == 'NPS_SURVEY',
        AutomationLog.sent_at >= cutoff,
        AutomationLog.clicked == True
    ).all()

    # Mapear respostas para scores (Excelente=10, Boa=8, Regular=5, Ruim=2)
    score_map = {
        'nps_excelente': 10,
        'nps_boa': 8,
        'nps_regular': 5,
        'nps_ruim': 2
    }

    scores = []
    for log in nps_logs:
        response = getattr(log, 'response_data', None)
        if response and response in score_map:
            scores.append(score_map[response])
        elif log.clicked:
            scores.append(7)  # Default para clicados sem resposta especifica

    avg_nps = round(sum(scores) / len(scores), 1) if scores else 0
    total_responses = len(scores)
    total_sent = AutomationLog.query.filter(
        AutomationLog.automation_type == 'NPS_SURVEY',
        AutomationLog.sent_at >= cutoff
    ).count()

    return jsonify({
        'avg_nps': avg_nps,
        'total_responses': total_responses,
        'total_sent': total_sent,
        'response_rate': round(total_responses / total_sent * 100, 1) if total_sent > 0 else 0
    })


@crm_api_bp.route('/settings/automation', methods=['GET', 'POST'])
@login_required
def automation_settings():
    """GET: retorna estado dos toggles. POST: salva um toggle."""
    if not current_user.is_admin and current_user.role != 'manager':
        return jsonify({'error': 'Unauthorized'}), 403

    if request.method == 'POST':
        data = request.json
        key = data.get('key')
        value = data.get('value')

        valid_keys = ['automation_welcome', 'automation_recovery', 'automation_nps']
        if key not in valid_keys:
            return jsonify({'success': False, 'error': 'Chave invalida'}), 400

        SystemConfig.set(key, str(value).lower(), description=f'Toggle automacao {key}')
        return jsonify({'success': True})

    return jsonify({
        'welcome': SystemConfig.get('automation_welcome', 'true') == 'true',
        'recovery': SystemConfig.get('automation_recovery', 'true') == 'true',
        'nps': SystemConfig.get('automation_nps', 'true') == 'true'
    })
