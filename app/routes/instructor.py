# app/routes/instructor.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, jsonify
from flask_login import login_required, current_user
from app.models import ClassSchedule, Booking, BookingStatus, User, Modality
from app import db
from datetime import datetime, timedelta, time, date

instructor_bp = Blueprint('instructor', __name__, url_prefix='/instructor')

WEEKDAYS = [
    (0, 'Domingo'),
    (1, 'Segunda-feira'),
    (2, 'Terça-feira'),
    (3, 'Quarta-feira'),
    (4, 'Quinta-feira'),
    (5, 'Sexta-feira'),
    (6, 'Sábado')
]

def instructor_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(403)
        # Permite acesso para Instrutor, Tecnica e Nutrologo (baseado no role ou professional_type)
        is_staff = current_user.role in ('instructor', 'admin') or \
                   (hasattr(current_user, 'professional_type') and current_user.professional_type is not None)
        
        if not is_staff:
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

    # Metricas do dia
    all_bookings_today = Booking.query.join(ClassSchedule).filter(
        ClassSchedule.instructor_id == current_user.id,
        Booking.date == selected_date
    ).all()

    day_metrics = {
        'total': len(all_bookings_today),
        'confirmed': sum(1 for b in all_bookings_today if b.status == BookingStatus.CONFIRMED),
        'completed': sum(1 for b in all_bookings_today if b.status == BookingStatus.COMPLETED),
        'no_show': sum(1 for b in all_bookings_today if b.status == BookingStatus.NO_SHOW),
        'cancelled': sum(1 for b in all_bookings_today if b.status == BookingStatus.CANCELLED),
    }

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
                         current_time=current_time,
                         day_metrics=day_metrics)

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

    # Observacoes do aluno
    from app.models.student_note import StudentNote, NoteType
    student_notes = StudentNote.query.filter_by(
        student_id=student.id
    ).order_by(StudentNote.created_at.desc()).limit(20).all()

    # Ultimos registros de carga
    from app.models.workout_log import WorkoutLog
    recent_logs = WorkoutLog.query.filter_by(
        user_id=student.id
    ).order_by(WorkoutLog.logged_at.desc()).limit(10).all()

    # Exercicios do plano ativo (para select de registro de carga)
    plan_exercises = []
    if active_plan:
        for ws in active_plan.workout_sessions:
            for we in ws.exercises:
                if we.exercise not in plan_exercises:
                    plan_exercises.append(we.exercise)

    return render_template('instructor/students/detail.html',
                          student=student,
                          active_plan=active_plan,
                          past_plans=past_plans,
                          parq=parq,
                          ems=ems,
                          bookings=bookings,
                          pain_alert=pain_alert,
                          whatsapp_logs=whatsapp_logs,
                          student_notes=student_notes,
                          recent_logs=recent_logs,
                          plan_exercises=plan_exercises,
                          NoteType=NoteType)


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


# ==================== WORKOUT LOG (REGISTRO DE CARGA) ====================

@instructor_bp.route('/student/<int:student_id>/log-workout', methods=['POST'])
@login_required
@instructor_required
def log_workout(student_id):
    """Registrar carga/performance de um exercicio."""
    from app.models.workout_log import WorkoutLog
    from app.models.training import Exercise

    student = User.query.get_or_404(student_id)
    exercise_id = request.form.get('exercise_id', type=int)
    weight_kg = request.form.get('weight_kg', type=float)
    reps = request.form.get('reps', type=int)
    sets = request.form.get('sets', type=int)
    notes = request.form.get('notes', '')

    if not exercise_id:
        flash('Selecione um exercicio.', 'danger')
        return redirect(url_for('instructor.student_detail', id=student_id))

    log = WorkoutLog(
        user_id=student_id,
        exercise_id=exercise_id,
        instructor_id=current_user.id,
        weight_kg=weight_kg,
        reps=reps,
        sets=sets,
        notes=notes
    )
    db.session.add(log)
    db.session.commit()

    flash('Carga registrada com sucesso!', 'success')
    return redirect(url_for('instructor.student_detail', id=student_id))


@instructor_bp.route('/student/<int:student_id>/workout-history/<int:exercise_id>')
@login_required
@instructor_required
def workout_history_api(student_id, exercise_id):
    """API: historico de carga de um exercicio."""
    from app.models.workout_log import WorkoutLog

    logs = WorkoutLog.query.filter_by(
        user_id=student_id,
        exercise_id=exercise_id
    ).order_by(WorkoutLog.logged_at.desc()).limit(20).all()

    return jsonify([{
        'date': log.logged_at.strftime('%d/%m/%Y'),
        'weight_kg': log.weight_kg,
        'reps': log.reps,
        'sets': log.sets,
        'notes': log.notes
    } for log in logs])


# ==================== OBSERVACOES POR ALUNO ====================

@instructor_bp.route('/student/<int:student_id>/add-note', methods=['POST'])
@login_required
@instructor_required
def add_student_note(student_id):
    """Adicionar observacao sobre o aluno."""
    from app.models.student_note import StudentNote, NoteType

    student = User.query.get_or_404(student_id)
    content = request.form.get('content', '').strip()
    note_type_str = request.form.get('note_type', 'general')

    if not content:
        flash('A observacao nao pode estar vazia.', 'danger')
        return redirect(url_for('instructor.student_detail', id=student_id))

    try:
        note_type = NoteType(note_type_str)
    except ValueError:
        note_type = NoteType.GENERAL

    note = StudentNote(
        student_id=student_id,
        instructor_id=current_user.id,
        note_type=note_type,
        content=content
    )
    db.session.add(note)
    db.session.commit()

    flash('Observacao adicionada com sucesso!', 'success')
    return redirect(url_for('instructor.student_detail', id=student_id))


# ==================== QR CODE CHECK-IN ====================

@instructor_bp.route('/qr-checkin')
@login_required
@instructor_required
def qr_checkin():
    """Tela de leitura de QR Code para check-in."""
    return render_template('instructor/qr_checkin.html')


@instructor_bp.route('/api/qr-checkin', methods=['POST'])
@login_required
@instructor_required
def process_qr_checkin():
    """API: processar QR Code de check-in."""
    import hashlib
    data = request.get_json()
    qr_data = data.get('qr_data', '')

    # QR format: "checkin:{user_id}:{date}:{token}"
    parts = qr_data.split(':')
    if len(parts) != 4 or parts[0] != 'checkin':
        return jsonify({'success': False, 'error': 'QR Code invalido'})

    try:
        user_id = int(parts[1])
        qr_date = parts[2]
        token = parts[3]
    except (ValueError, IndexError):
        return jsonify({'success': False, 'error': 'QR Code invalido'})

    # Validate date (must be today)
    today_str = datetime.now().strftime('%Y-%m-%d')
    if qr_date != today_str:
        return jsonify({'success': False, 'error': 'QR Code expirado (data diferente)'})

    # Validate token
    student = User.query.get(user_id)
    if not student or student.role != 'student':
        return jsonify({'success': False, 'error': 'Aluno nao encontrado'})

    expected_token = hashlib.sha256(f"{user_id}:{qr_date}:{student.password_hash[:10]}".encode()).hexdigest()[:12]
    if token != expected_token:
        return jsonify({'success': False, 'error': 'QR Code invalido'})

    # Find today's booking for this student with this instructor
    today = datetime.now().date()
    booking = Booking.query.join(ClassSchedule).filter(
        Booking.user_id == user_id,
        Booking.date == today,
        Booking.status == BookingStatus.CONFIRMED,
        ClassSchedule.instructor_id == current_user.id
    ).first()

    if not booking:
        return jsonify({'success': False, 'error': 'Nenhuma aula agendada para este aluno hoje'})

    booking.status = BookingStatus.COMPLETED
    db.session.commit()

    return jsonify({
        'success': True,
        'student_name': student.name,
        'message': f'Check-in de {student.name} realizado com sucesso!'
    })


# ==================== GERENCIAMENTO DE HORARIOS (AGENDAMENTO) ====================

@instructor_bp.route('/schedules')
@login_required
@instructor_required
def list_schedules():
    """Lista todos os horarios do sistema (Acesso total conforme solicitado)"""
    schedules = ClassSchedule.query.order_by(
        ClassSchedule.weekday,
        ClassSchedule.start_time
    ).all()

    # Agrupar por dia da semana
    schedules_by_day = {}
    for day_num, day_name in WEEKDAYS:
        schedules_by_day[day_name] = [s for s in schedules if s.weekday == day_num]

    return render_template('instructor/schedules/list.html',
                         schedules_by_day=schedules_by_day,
                         weekdays=WEEKDAYS)


@instructor_bp.route('/schedules/create', methods=['GET', 'POST'])
@login_required
@instructor_required
def create_schedule():
    """Criar novo horario (enviar para aprovação do admin)"""
    if request.method == 'POST':
        start_time_val = time.fromisoformat(request.form['start_time'])
        end_time_val = time.fromisoformat(request.form['end_time'])
        weekdays_selected = request.form.getlist('weekdays')

        if not weekdays_selected:
            flash('Selecione pelo menos um dia da semana.', 'danger')
            return redirect(url_for('instructor.create_schedule'))

        modality = Modality.query.get_or_404(int(request.form['modality_id']))
        instructor_id = int(request.form['instructor_id'])
        capacity = int(request.form['capacity'])
        duration = modality.default_duration

        created_count = 0
        dummy_date = date.today()
        dt_start = datetime.combine(dummy_date, start_time_val)
        dt_end = datetime.combine(dummy_date, end_time_val)
        
        current_time = dt_start
        while current_time + timedelta(minutes=duration) <= dt_end:
            slot_start = current_time.time()
            current_time += timedelta(minutes=duration)
            slot_end = current_time.time()
            
            for weekday in weekdays_selected:
                schedule = ClassSchedule(
                    modality_id=modality.id,
                    instructor_id=instructor_id,
                    weekday=int(weekday),
                    start_time=slot_start,
                    end_time=slot_end,
                    capacity=capacity,
                    is_active=True,
                    is_approved=False,  # Requer aprovação
                    created_by_id=current_user.id
                )
                db.session.add(schedule)
                created_count += 1

        db.session.commit()

        flash(f'{created_count} horários criados e enviados para aprovação do administrador!', 'success')
        return redirect(url_for('instructor.list_schedules'))

    modalities = Modality.query.filter_by(is_active=True).order_by(Modality.name).all()
    # No caso do instrutor, ele pode criar para si mesmo ou para outros? 
    # "Podendo cancelar aulas que eles abriram, ou que tem como seu nome de instrutor"
    # Sugere que eles podem ser instrutores. Vamos listar todos os instrutores ativos.
    instructors = User.query.filter(
        User.role.in_(['instructor', 'admin']),
        User.is_active == True
    ).order_by(User.name).all()

    return render_template('instructor/schedules/form.html',
                         schedule=None,
                         modalities=modalities,
                         instructors=instructors,
                         weekdays=WEEKDAYS)


@instructor_bp.route('/schedules/cancel/<int:id>', methods=['POST'])
@login_required
@instructor_required
def cancel_schedule_template(id):
    """Cancela (desabilita) um horário que o instrutor abriu ou é o instrutor"""
    schedule = ClassSchedule.query.get_or_404(id)
    
    # Regra: Pode cancelar se abriu OU se é o instrutor
    can_cancel = current_user.role == 'admin' or \
                 schedule.created_by_id == current_user.id or \
                 schedule.instructor_id == current_user.id
                 
    if not can_cancel:
        flash('Você não tem permissão para cancelar este horário.', 'danger')
        return redirect(url_for('instructor.list_schedules'))

    schedule.is_active = False
    db.session.commit()

    flash('Horário desativado com sucesso.', 'info')
    return redirect(url_for('instructor.list_schedules'))


