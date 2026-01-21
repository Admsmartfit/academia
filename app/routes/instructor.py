# app/routes/instructor.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app.models import ClassSchedule, Booking, BookingStatus, User
from app import db
from datetime import datetime

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
    """Dashboard do Instrutor - Lista de aulas de hoje"""
    today = datetime.now().date()
    weekday = today.weekday()
    # No sistema: 0=Dom, 1=Seg... 6=Sab
    # Python weekday: 0=Seg... 6=Dom
    sys_weekday = (weekday + 1) % 7

    # Buscar horários do instrutor hoje
    schedules = ClassSchedule.query.filter_by(
        instructor_id=current_user.id,
        weekday=sys_weekday,
        is_active=True
    ).order_by(ClassSchedule.start_time).all()

    # Para cada horário, buscar os agendamentos confirmados
    for sched in schedules:
        sched.today_bookings = Booking.query.filter_by(
            schedule_id=sched.id,
            date=today,
            status=BookingStatus.CONFIRMED
        ).all()

    return render_template('instructor/dashboard.html', schedules=schedules, today=today)

@instructor_bp.route('/checkin/<int:booking_id>', methods=['POST'])
@login_required
@instructor_required
def checkin(booking_id):
    """Realiza check-in do aluno"""
    booking = Booking.query.get_or_404(booking_id)
    
    # Verificar se a aula é do instrutor logado
    if booking.schedule.instructor_id != current_user.id:
        abort(403)
        
    if booking.status != BookingStatus.CONFIRMED:
        flash('Este agendamento não pode receber check-in.', 'warning')
        return redirect(url_for('instructor.dashboard'))

    booking.checkin()
    flash(f'Check-in realizado para {booking.user.name}!', 'success')
    return redirect(url_for('instructor.dashboard'))

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
    return redirect(url_for('instructor.dashboard'))
