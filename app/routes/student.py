# app/routes/student.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from flask import abort
from app.models import (
    Subscription, Payment, Booking, BookingStatus, SubscriptionStatus,
    PaymentStatusEnum, ClassSchedule, User, RecurringBooking, FrequencyType
)
from app import db
from datetime import datetime, timedelta
from sqlalchemy import func

student_bp = Blueprint('student', __name__, url_prefix='/student')


@student_bp.route('/')
@student_bp.route('/dashboard')
@login_required
def dashboard():
    """Dashboard do aluno"""
    # Buscar assinaturas ativas
    active_subscriptions = Subscription.query.filter_by(
        user_id=current_user.id,
        status=SubscriptionStatus.ACTIVE
    ).all()

    # Total de creditos disponiveis
    total_credits = sum(sub.credits_remaining for sub in active_subscriptions)

    # Proximas aulas
    today = datetime.now().date()
    upcoming_bookings = Booking.query.filter(
        Booking.user_id == current_user.id,
        Booking.date >= today,
        Booking.status == BookingStatus.CONFIRMED
    ).order_by(Booking.date, Booking.schedule_id).limit(5).all()

    # Proxima aula
    next_booking = upcoming_bookings[0] if upcoming_bookings else None

    # Pagamentos pendentes
    pending_payments = Payment.query.join(Subscription).filter(
        Subscription.user_id == current_user.id,
        Payment.status.in_([PaymentStatusEnum.PENDING, PaymentStatusEnum.OVERDUE])
    ).order_by(Payment.due_date).all()

    # Ranking do usuario
    user_rank = db.session.query(
        func.count(User.id)
    ).filter(
        User.role == 'student',
        User.xp > current_user.xp
    ).scalar() + 1

    # Total de aulas completadas
    total_classes = Booking.query.filter_by(
        user_id=current_user.id,
        status=BookingStatus.COMPLETED
    ).count()

    return render_template('student/dashboard.html',
                         active_subscriptions=active_subscriptions,
                         total_credits=total_credits,
                         upcoming_bookings=upcoming_bookings,
                         next_booking=next_booking,
                         pending_payments=pending_payments,
                         user_rank=user_rank,
                         total_classes=total_classes)


@student_bp.route('/subscriptions')
@login_required
def my_subscriptions():
    """Minhas assinaturas e pagamentos"""
    subscriptions = Subscription.query.filter_by(
        user_id=current_user.id
    ).order_by(Subscription.created_at.desc()).all()

    return render_template('student/my_subscriptions.html', subscriptions=subscriptions)


@student_bp.route('/subscription/<int:id>')
@login_required
def subscription_detail(id):
    """Detalhes de uma assinatura"""
    subscription = Subscription.query.filter_by(
        id=id,
        user_id=current_user.id
    ).first_or_404()

    return render_template('student/subscription_detail.html', subscription=subscription)


@student_bp.route('/schedule')
@login_required
def schedule():
    """Grade de agendamento"""

    # Data selecionada (hoje por padrao)
    selected_date_str = request.args.get('date')
    if selected_date_str:
        try:
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = datetime.now().date()
    else:
        selected_date = datetime.now().date()

    # Nao permitir agendar no passado
    if selected_date < datetime.now().date():
        selected_date = datetime.now().date()

    # Dia da semana (0=dom no nosso sistema, 6=sab)
    # Python: 0=segunda, 6=domingo
    weekday = selected_date.weekday()
    if weekday == 6:  # Domingo no Python = 6, queremos 0
        weekday = 0
    else:
        weekday += 1  # Segunda=1, Terca=2, etc.

    # Buscar aulas do dia
    schedules = ClassSchedule.query.filter_by(
        weekday=weekday,
        is_active=True
    ).order_by(ClassSchedule.start_time).all()

    # Adicionar info de vagas e status do usuario
    for sched in schedules:
        sched.current_bookings = Booking.query.filter_by(
            schedule_id=sched.id,
            date=selected_date,
            status=BookingStatus.CONFIRMED
        ).count()
        sched.available_spots = sched.capacity - sched.current_bookings

        # Verificar se usuario ja agendou
        sched.user_booked = Booking.query.filter_by(
            user_id=current_user.id,
            schedule_id=sched.id,
            date=selected_date,
            status=BookingStatus.CONFIRMED
        ).first()

    # Assinaturas ativas para selecao
    active_subscriptions = Subscription.query.filter_by(
        user_id=current_user.id,
        status=SubscriptionStatus.ACTIVE
    ).filter(
        Subscription.credits_used < Subscription.credits_total
    ).all()

    # Calcular datas da semana para navegacao
    week_dates = []
    start_of_week = selected_date - timedelta(days=selected_date.weekday())
    for i in range(7):
        week_dates.append(start_of_week + timedelta(days=i))

    return render_template('student/schedule.html',
        schedules=schedules,
        selected_date=selected_date,
        active_subscriptions=active_subscriptions,
        week_dates=week_dates
    )


@student_bp.route('/book/<int:schedule_id>', methods=['POST'])
@login_required
def book_class(schedule_id):
    """Agendar uma aula"""

    schedule = ClassSchedule.query.get_or_404(schedule_id)
    date_str = request.form.get('date')
    subscription_id = request.form.get('subscription_id')

    if not date_str or not subscription_id:
        flash('Dados incompletos para agendamento.', 'danger')
        return redirect(url_for('student.schedule'))

    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        subscription_id = int(subscription_id)
    except ValueError:
        flash('Data ou assinatura invalida.', 'danger')
        return redirect(url_for('student.schedule'))

    subscription = Subscription.query.filter_by(
        id=subscription_id,
        user_id=current_user.id
    ).first_or_404()

    # Validar agendamento
    can_book, error_msg = Booking.validate_booking(current_user, schedule, date, subscription)

    if not can_book:
        flash(error_msg, 'danger')
        return redirect(url_for('student.schedule', date=date_str))

    # Verificar se a data esta dentro da validade da assinatura
    if date > subscription.end_date:
        flash(f'Esta data esta fora da validade do seu pacote (ate {subscription.end_date.strftime("%d/%m/%Y")}).', 'danger')
        return redirect(url_for('student.schedule', date=date_str))

    # Criar agendamento
    booking = Booking(
        user_id=current_user.id,
        subscription_id=subscription.id,
        schedule_id=schedule.id,
        date=date,
        status=BookingStatus.CONFIRMED,
        is_recurring=False,
        cost_at_booking=schedule.modality.credits_cost
    )

    db.session.add(booking)

    # Debitar credito
    subscription.credits_used += schedule.modality.credits_cost

    db.session.commit()

    flash(f'Aula agendada com sucesso! {schedule.modality.name} em {date.strftime("%d/%m/%Y")} as {schedule.start_time.strftime("%H:%M")}', 'success')
    return redirect(url_for('student.my_bookings'))


@student_bp.route('/cancel-booking/<int:booking_id>', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    """Cancelar uma aula agendada"""

    booking = Booking.query.filter_by(
        id=booking_id,
        user_id=current_user.id,
        status=BookingStatus.CONFIRMED
    ).first_or_404()

    # Verificar se pode cancelar (2h de antecedencia)
    if not booking.can_cancel:
        flash('Nao e possivel cancelar com menos de 2 horas de antecedencia.', 'danger')
        return redirect(url_for('student.my_bookings'))

    # Calcular penalidade de XP
    class_datetime = datetime.combine(booking.date, booking.schedule.start_time)
    time_until = class_datetime - datetime.now()
    xp_penalty = 0

    if time_until < timedelta(hours=3):
        # Cancelou entre 2-3h antes = -5 XP
        xp_penalty = 5
        current_user.xp = max(0, current_user.xp - xp_penalty)

    # Cancelar agendamento
    try:
        booking.cancel(reason=request.form.get('reason', 'Cancelamento pelo aluno'))
        # Obs: booking.cancel ja estorna o credito usando cost_at_booking
    except ValueError as e:
        flash(str(e), 'danger')
        return redirect(url_for('student.my_bookings'))

    # Aplicar penalidade de XP se houver
    if xp_penalty > 0:
        current_user.xp = max(0, current_user.xp - xp_penalty)
        db.session.commit()

    if xp_penalty > 0:
        flash(f'Aula cancelada. Credito estornado. Voce perdeu {xp_penalty} XP por cancelar proximo do horario.', 'warning')
    else:
        flash('Aula cancelada com sucesso. Credito estornado.', 'success')

    return redirect(url_for('student.my_bookings'))


@student_bp.route('/my-bookings')
@login_required
def my_bookings():
    """Minhas aulas agendadas"""

    today = datetime.now().date()

    # Futuras
    upcoming = Booking.query.filter(
        Booking.user_id == current_user.id,
        Booking.date >= today,
        Booking.status == BookingStatus.CONFIRMED
    ).order_by(Booking.date, Booking.schedule_id).all()

    # Passadas (ultimas 20)
    past = Booking.query.filter(
        Booking.user_id == current_user.id,
        Booking.status.in_([BookingStatus.COMPLETED, BookingStatus.CANCELLED, BookingStatus.NO_SHOW])
    ).order_by(Booking.date.desc()).limit(20).all()

    return render_template('student/my_bookings.html',
        upcoming=upcoming,
        past=past
    )


@student_bp.route('/ranking')
@login_required
def ranking():
    """Ranking de alunos"""

    # Top 10
    top_users = User.query.filter_by(
        role='student',
        is_active=True
    ).order_by(User.xp.desc()).limit(10).all()

    # Posicao do usuario
    user_rank = db.session.query(
        func.count(User.id)
    ).filter(
        User.role == 'student',
        User.xp > current_user.xp
    ).scalar() + 1

    # XP necessario para proxima posicao
    next_user = User.query.filter(
        User.role == 'student',
        User.xp > current_user.xp
    ).order_by(User.xp).first()

    xp_to_next = (next_user.xp - current_user.xp) if next_user else 0

    # Total de alunos
    total_students = User.query.filter_by(role='student', is_active=True).count()

    return render_template('student/ranking.html',
        top_users=top_users,
        user_rank=user_rank,
        xp_to_next=xp_to_next,
        total_students=total_students
    )


# ==================== AGENDAMENTO RECORRENTE ====================

@student_bp.route('/recurring/create', methods=['GET', 'POST'])
@login_required
def create_recurring():
    """Criar agendamento recorrente"""

    if request.method == 'POST':
        schedule_id = request.form.get('schedule_id')
        subscription_id = request.form.get('subscription_id')
        frequency = request.form.get('frequency')
        start_date_str = request.form.get('start_date')

        if not all([schedule_id, subscription_id, frequency, start_date_str]):
            flash('Preencha todos os campos obrigatorios.', 'danger')
            return redirect(url_for('student.create_recurring'))

        try:
            schedule_id = int(schedule_id)
            subscription_id = int(subscription_id)
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Dados invalidos.', 'danger')
            return redirect(url_for('student.create_recurring'))

        # Validacoes
        subscription = Subscription.query.filter_by(
            id=subscription_id,
            user_id=current_user.id
        ).first_or_404()

        schedule = ClassSchedule.query.get_or_404(schedule_id)

        if subscription.is_blocked:
            flash('Sua assinatura esta bloqueada por falta de pagamento.', 'danger')
            return redirect(url_for('student.my_subscriptions'))

        cost = schedule.modality.credits_cost
        if subscription.credits_remaining < cost:
            flash(f'Voce precisa de pelo menos {cost} creditos para criar agendamento recorrente.', 'warning')
            return redirect(url_for('student.schedule'))

        if start_date < datetime.now().date():
            flash('A data de inicio nao pode ser no passado.', 'danger')
            return redirect(url_for('student.create_recurring'))

        if start_date > subscription.end_date:
            flash('A data de inicio deve estar dentro da validade da sua assinatura.', 'danger')
            return redirect(url_for('student.create_recurring'))

        # Verificar se ja existe recorrencia ativa para este horario
        existing = RecurringBooking.query.filter_by(
            user_id=current_user.id,
            schedule_id=schedule_id,
            is_active=True
        ).first()

        if existing:
            flash('Voce ja possui um agendamento recorrente ativo para este horario.', 'warning')
            return redirect(url_for('student.my_recurring'))

        # Criar recorrencia
        recurring = RecurringBooking(
            user_id=current_user.id,
            subscription_id=subscription_id,
            schedule_id=schedule_id,
            frequency=FrequencyType[frequency],
            start_date=start_date,
            end_date=subscription.end_date,
            next_occurrence=start_date,
            is_active=True
        )

        db.session.add(recurring)
        db.session.commit()

        # Criar primeiro agendamento
        first_booking = recurring.create_next_booking()

        if first_booking:
            flash('Agendamento recorrente criado! Primeira aula agendada automaticamente.', 'success')
        else:
            flash('Agendamento recorrente criado! As aulas serao agendadas automaticamente.', 'success')

        return redirect(url_for('student.my_recurring'))

    # GET: Mostrar formulario
    active_subscriptions = Subscription.query.filter_by(
        user_id=current_user.id,
        status=SubscriptionStatus.ACTIVE
    ).filter(
        (Subscription.credits_total - Subscription.credits_used) >= 4
    ).all()

    schedules = ClassSchedule.query.filter_by(is_active=True).order_by(
        ClassSchedule.weekday, ClassSchedule.start_time
    ).all()

    return render_template('student/recurring_form.html',
                         subscriptions=active_subscriptions,
                         schedules=schedules)


@student_bp.route('/recurring/list')
@login_required
def my_recurring():
    """Listar agendamentos recorrentes"""
    recurring_bookings = RecurringBooking.query.filter_by(
        user_id=current_user.id
    ).order_by(RecurringBooking.is_active.desc(), RecurringBooking.created_at.desc()).all()

    return render_template('student/recurring_list.html', recurring_bookings=recurring_bookings)


@student_bp.route('/recurring/<int:id>/cancel', methods=['POST'])
@login_required
def cancel_recurring(id):
    """Cancelar agendamento recorrente"""
    recurring = RecurringBooking.query.get_or_404(id)

    if recurring.user_id != current_user.id:
        abort(403)

    recurring.is_active = False
    db.session.commit()

    flash('Agendamento recorrente cancelado. Aulas ja agendadas nao foram afetadas.', 'info')
    return redirect(url_for('student.my_recurring'))
