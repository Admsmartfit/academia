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

    # Para cada horário, buscar todos os agendamentos (confirmados, completed, no_show)
    for sched in schedules:
        sched.today_bookings = Booking.query.filter(
            Booking.schedule_id == sched.id,
            Booking.date == selected_date,
            Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.COMPLETED, BookingStatus.NO_SHOW])
        ).all()

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


