# app/routes/instructor.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, jsonify
from flask_login import login_required, current_user
from app.models import ClassSchedule, Booking, BookingStatus, User
from app import db
from datetime import datetime, timedelta

instructor_bp = Blueprint('instructor', __name__, url_prefix='/instructor')

def instructor_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'instructor':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def instructor_or_totem_required(f):
    """Permite acesso para instrutores ou usuarios de terminal (totem)."""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(403)
        if current_user.role not in ('instructor', 'totem', 'admin'):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@instructor_bp.route('/')
@instructor_bp.route('/dashboard')
@login_required
@instructor_required
def dashboard():
    """Dashboard do Instrutor - Lista de aulas com navegação de datas"""
    # Pega a data da query string ou usa hoje
    date_str = request.args.get('date')
    if date_str:
        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = datetime.now().date()
    else:
        selected_date = datetime.now().date()

    today = datetime.now().date()
    weekday = selected_date.weekday()
    # No sistema: 0=Dom, 1=Seg... 6=Sab
    # Python weekday: 0=Seg... 6=Dom
    sys_weekday = (weekday + 1) % 7

    # Buscar horários do instrutor para este dia
    schedules = ClassSchedule.query.filter_by(
        instructor_id=current_user.id,
        weekday=sys_weekday,
        is_active=True
    ).order_by(ClassSchedule.start_time).all()

    for sched in schedules:
        sched.today_bookings = Booking.query.filter(
            Booking.schedule_id == sched.id,
            Booking.date == selected_date,
            Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.COMPLETED, BookingStatus.NO_SHOW])
        ).all()
        
        # Adicionar status de saude para cada booking
        from app.models.health import ScreeningType
        for booking in sched.today_bookings:
            booking.user.parq_status = booking.user.get_screening_status(ScreeningType.PARQ)
            booking.user.ems_status = booking.user.get_screening_status(ScreeningType.EMS)

    # Datas de navegação
    prev_date = selected_date - timedelta(days=1)
    next_date = selected_date + timedelta(days=1)

    # Horário atual (para destacar)
    now = datetime.now()
    current_time = now.time() if selected_date == today else None

    return render_template('instructor/dashboard.html',
                         schedules=schedules,
                         selected_date=selected_date,
                         today=today,
                         prev_date=prev_date,
                         next_date=next_date,
                         current_time=current_time)

# Check-in removido - sistema considera presença automaticamente

@instructor_bp.route('/noshow/<int:booking_id>', methods=['POST'])
@login_required
@instructor_required
def no_show(booking_id):
    """Marca falta (no-show) do aluno"""
    booking = Booking.query.get_or_404(booking_id)

    if booking.schedule.instructor_id != current_user.id:
        abort(403)

    booking.status = BookingStatus.NO_SHOW
    db.session.commit()

    flash(f'Falta registrada para {booking.user.name}.', 'info')
    return redirect(request.referrer or url_for('instructor.dashboard'))

# Criar agendamento removido - apenas alunos podem agendar

@instructor_bp.route('/cancel-booking/<int:booking_id>', methods=['POST'])
@login_required
@instructor_required
def cancel_booking(booking_id):
    """Cancela agendamento com motivo"""
    booking = Booking.query.get_or_404(booking_id)

    if booking.schedule.instructor_id != current_user.id:
        abort(403)

    reason = request.form.get('reason', '').strip()

    if not reason:
        flash('Motivo do cancelamento é obrigatório.', 'warning')
        return redirect(request.referrer or url_for('instructor.dashboard'))

    booking.status = BookingStatus.CANCELLED
    booking.cancelled_at = datetime.utcnow()
    booking.cancellation_reason = f"[Instrutor] {reason}"

    # Estornar crédito se houver subscription
    if booking.subscription:
        booking.subscription.refund_credit(booking.cost_at_booking)

    db.session.commit()

    flash(f'Agendamento de {booking.user.name} cancelado.', 'info')
    return redirect(request.referrer or url_for('instructor.dashboard'))

@instructor_bp.route('/bulk-cancel', methods=['POST'])
@login_required
@instructor_required
def bulk_cancel():
    """Cancela múltiplos agendamentos"""
    booking_ids = request.form.getlist('booking_ids[]')
    reason = request.form.get('reason', '').strip()

    if not reason:
        flash('Motivo do cancelamento é obrigatório.', 'warning')
        return redirect(request.referrer or url_for('instructor.dashboard'))

    if not booking_ids:
        flash('Nenhum agendamento selecionado.', 'warning')
        return redirect(request.referrer or url_for('instructor.dashboard'))

    # Buscar bookings
    bookings = Booking.query.filter(
        Booking.id.in_(booking_ids),
        Booking.status == BookingStatus.CONFIRMED
    ).all()

    # Verificar se todos são do instrutor
    for booking in bookings:
        if booking.schedule.instructor_id != current_user.id:
            abort(403)

    count = 0
    for booking in bookings:
        booking.status = BookingStatus.CANCELLED
        booking.cancelled_at = datetime.utcnow()
        booking.cancellation_reason = f"[Instrutor - Cancelamento em Lote] {reason}"

        # Estornar crédito
        if booking.subscription:
            booking.subscription.refund_credit(booking.cost_at_booking)

        count += 1

    db.session.commit()

    flash(f'{count} agendamento(s) cancelado(s).', 'success')
    return redirect(request.referrer or url_for('instructor.dashboard'))

@instructor_bp.route('/log-ems/<int:booking_id>', methods=['POST'])
@login_required
@instructor_required
def log_ems_session(booking_id):
    """Registra parâmetros de uma sessão EMS ou Eletrolipólise"""
    from app.models.health import EMSSessionLog, ScreeningType
    
    booking = Booking.query.get_or_404(booking_id)
    
    if booking.schedule.instructor_id != current_user.id:
        abort(403)
        
    # Verificar se é uma modalidade que exige log
    # Por enquanto assumimos FES ou Eletrolipólise
    procedure_type = ScreeningType.EMS if "FES" in booking.schedule.modality.name else ScreeningType.ELETROLIPO
    
    log = EMSSessionLog(
        booking_id=booking.id,
        user_id=booking.user_id,
        instructor_id=current_user.id,
        procedure_type=procedure_type,
        frequency_hz=request.form.get('frequency', type=int),
        intensity_ma=request.form.get('intensity', type=int),
        duration_minutes=request.form.get('duration', type=int),
        treatment_area=request.form.get('area'),
        discomfort_reported=request.form.get('discomfort') == 'on',
        notes=request.form.get('notes')
    )
    
    # Marcar aula como concluída se já começou
    if booking.status == BookingStatus.CONFIRMED:
        booking.status = BookingStatus.COMPLETED
    
    db.session.add(log)
    db.session.commit()
    
    flash(f'Sessão de {booking.user.name} registrada com sucesso!', 'success')
    return redirect(request.referrer or url_for('instructor.dashboard'))

@instructor_bp.route('/totem')
@login_required
@instructor_or_totem_required
def totem_view():
    """Interface do totem de reconhecimento facial (modo kiosk)."""
    return render_template('instructor/totem.html')


@instructor_bp.route('/training/prescribe')
@login_required
@instructor_required
def training_prescribe():
    """Interface de prescricao de treino para instrutor."""
    student_id = request.args.get('student_id')
    template_id = request.args.get('template_id')
    is_template = request.args.get('is_template') == '1'
    
    student = None
    if student_id:
        student = User.query.get(student_id)
        if student and student.role != 'student':
            student = None
            
    return render_template('instructor/training/prescribe.html', 
                         student=student, 
                         template_id=template_id,
                         is_template=is_template)


@instructor_bp.route('/training/list')
@login_required
@instructor_required
def training_list():
    """Lista de prescricoes de treino do instrutor."""
    from app.models.training import TrainingPlan
    plans = TrainingPlan.query.filter_by(
        instructor_id=current_user.id
    ).order_by(TrainingPlan.created_at.desc()).all()
    return render_template('instructor/training/list.html', plans=plans)


@instructor_bp.route('/training/templates')
@login_required
@instructor_required
def list_templates():
    """Lista modelos de treino (templates)."""
    from app.models.training import TrainingTemplate
    templates = TrainingTemplate.query.filter(
        db.or_(
            TrainingTemplate.instructor_id == current_user.id,
            TrainingTemplate.is_public == True
        )
    ).order_by(TrainingTemplate.name).all()
    return render_template('instructor/training/templates.html', templates=templates)


@instructor_bp.route('/training/<int:plan_id>')
@login_required
@instructor_required
def training_detail(plan_id):
    """Visualizacao detalhada de um plano de treino."""
    from app.models.training import TrainingPlan
    plan = TrainingPlan.query.get_or_404(plan_id)
    if plan.instructor_id != current_user.id and current_user.role != 'admin':
        abort(403)
    return render_template('instructor/training/detail.html', plan=plan)


@instructor_bp.route('/validate-checklist/<int:booking_id>', methods=['POST'])
@login_required
@instructor_required
def validate_checklist(booking_id):
    """
    Valida o checklist pré-sessão de Eletrolipólise.
    Verifica hidratação, jejum e regra de 48h na área.
    """
    from app.services.screening_service import ScreeningService
    
    booking = Booking.query.get_or_404(booking_id)
    
    # 1. Verificar inputs básicos
    hydration = request.form.get('hydration') == 'on'
    no_fasting = request.form.get('no_fasting') == 'on'
    area = request.form.get('area')
    
    if not hydration or not no_fasting:
        flash('O aluno deve estar hidratado e alimentado para realizar o procedimento.', 'danger')
        return redirect(request.referrer or url_for('instructor.dashboard'))
        
    if not area:
        flash('Informe a área de tratamento para verificar o intervalo de 48h.', 'warning')
        return redirect(request.referrer or url_for('instructor.dashboard'))
        
    # 2. Verificar regra de 48h
    can_proceed, msg = ScreeningService.can_book_ems_session(
        booking.user_id, 
        area, 
        datetime.utcnow()
    )
    
    if not can_proceed:
        flash(f'BLOQUEADO: {msg} ⛔', 'danger')
        return redirect(request.referrer or url_for('instructor.dashboard'))
        
    # 3. Se passou, registra nas notas do booking que o checklist foi feito
    timestamp = datetime.now().strftime('%d/%m %H:%M')
    checklist_note = f"[Checklist {timestamp}] Área: {area} | Hidratação: OK | Jejum: OK"
    
    if booking.notes:
        booking.notes += f"\n{checklist_note}"
    else:
        booking.notes = checklist_note
        
    db.session.commit()
    
    flash(f'Checklist APROVADO! Pode iniciar a sessão na área: {area}. ✅', 'success')
    return redirect(request.referrer or url_for('instructor.dashboard'))


@instructor_bp.route('/students')
@login_required
@instructor_required
def list_students():
    """Lista de alunos para o instrutor"""
    search = request.args.get('search', '')
    if search:
        students = User.query.filter(
            User.role == 'student',
            User.is_active == True,
            (User.name.ilike(f'%{search}%')) | (User.email.ilike(f'%{search}%'))
        ).order_by(User.name).all()
    else:
        students = User.query.filter_by(role='student', is_active=True).order_by(User.name).limit(50).all()
    
    return render_template('instructor/students/list.html', students=students, search=search)


@instructor_bp.route('/student/<int:id>')
@login_required
@instructor_required
def student_detail(id):
    """Detalhes do aluno para o instrutor (saude, treinos, historico)"""
    student = User.query.get_or_404(id)
    if student.role != 'student':
        abort(403)
        
    # Buscar treinos
    from app.models.training import TrainingPlan
    active_plan = TrainingPlan.query.filter_by(user_id=student.id, is_active=True).first()
    past_plans = TrainingPlan.query.filter_by(user_id=student.id, is_active=False).order_by(TrainingPlan.created_at.desc()).all()
    
    # Buscar triagens
    from app.models.health import HealthScreening, ScreeningType
    parq = HealthScreening.query.filter_by(user_id=student.id, screening_type=ScreeningType.PARQ).order_by(HealthScreening.created_at.desc()).first()
    ems = HealthScreening.query.filter_by(user_id=student.id, screening_type=ScreeningType.EMS).order_by(HealthScreening.created_at.desc()).first()
    
    # Alerta de Dor (Ultimas 48h)
    from app.models.crm import AutomationLog
    pain_alert = AutomationLog.query.filter(
        AutomationLog.user_id == student.id,
        AutomationLog.automation_type == 'pain_report',
        AutomationLog.sent_at >= datetime.utcnow() - timedelta(hours=48)
    ).first()

    # Logs de WhatsApp
    from app.models.whatsapp_log import WhatsAppLog
    whatsapp_logs = WhatsAppLog.query.filter_by(
        user_id=student.id
    ).order_by(WhatsAppLog.created_at.desc()).limit(15).all()
    
    # Historico de aulas
    bookings = Booking.query.filter_by(user_id=student.id).order_by(Booking.date.desc()).limit(20).all()
    
    return render_template('instructor/students/detail.html', 
                          student=student, 
                          active_plan=active_plan,
                          past_plans=past_plans,
                          parq=parq,
                          ems=ems,
                          bookings=bookings,
                          pain_alert=pain_alert,
                          whatsapp_logs=whatsapp_logs)


@instructor_bp.route('/student/<int:id>/face', methods=['GET'])
@login_required
@instructor_required
def face_enrollment(id):
    """Pagina de cadastro facial pelo instrutor"""
    student = User.query.get_or_404(id)
    if student.role != 'student':
        abort(403)
    return render_template('instructor/students/face_enrollment.html', student=student)


@instructor_bp.route('/student/<int:id>/face/enroll', methods=['POST'])
@login_required
@instructor_required
def enroll_face(id):
    """API para instrutor cadastrar face do aluno"""
    from app.services.face_service import FaceRecognitionService
    
    student = User.query.get_or_404(id)
    data = request.get_json()
    
    if not data or 'image' not in data:
        return jsonify({'success': False, 'error': 'Imagem nao fornecida'}), 400
        
    face_service = FaceRecognitionService(tolerance=0.6)
    result = face_service.enroll_face(student.id, data['image'])
    
    if result['success']:
        return jsonify({
            'success': True, 
            'message': f'Face de {student.name} cadastrada com sucesso!',
            'confidence': result['confidence']
        }), 201
    else:
        return jsonify({'success': False, 'error': result['message']}), 400


