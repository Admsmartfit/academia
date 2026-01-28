# app/routes/student.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from flask import abort
from app.models import (
    Subscription, Payment, Booking, BookingStatus, SubscriptionStatus,
    PaymentStatusEnum, ClassSchedule, User, RecurringBooking, FrequencyType,
    ConversionRule, CreditWallet, ScheduleSlotGender, Gender, ScreeningType
)
from app.models.xp_ledger import XPLedger
from app.services.credit_service import CreditService
from app.services.gender_distribution_service import GenderDistributionService
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

    # Total de creditos disponiveis (assinaturas + wallets)
    subscription_credits = sum(sub.credits_remaining for sub in active_subscriptions)
    wallet_credits = CreditWallet.get_user_total_credits(current_user.id)
    total_credits = subscription_credits + wallet_credits

    # Creditos expirando em 7 dias
    expiring_wallets = CreditWallet.get_expiring_soon(current_user.id, days=7)
    expiring_credits = sum(w.credits_remaining for w in expiring_wallets)

    # XP disponivel para conversao
    xp_available = XPLedger.get_user_available_xp(current_user.id)

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

    # Status da triagem de saúde
    screening_status = current_user.get_screening_status(ScreeningType.PARQ)

    return render_template('student/dashboard.html',
                         active_subscriptions=active_subscriptions,
                         total_credits=total_credits,
                         wallet_credits=wallet_credits,
                         expiring_credits=expiring_credits,
                         xp_available=xp_available,
                         upcoming_bookings=upcoming_bookings,
                         next_booking=next_booking,
                         pending_payments=pending_payments,
                         user_rank=user_rank,
                         total_classes=total_classes,
                         screening_status=screening_status)


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

            # Verificar genero
            sched.gender_restricted = False
            sched.slot_gender = None
            sched.gender_message = None

            if sched.modality.requires_gender_segregation:
                can_book, msg = GenderDistributionService.can_user_book_slot(
                    current_user, sched.id, selected_date
                )
                if not can_book:
                    sched.gender_restricted = True
                    sched.gender_message = msg

                # Obter genero do slot para exibicao
                slot_gender = ScheduleSlotGender.get_slot_gender(sched.id, selected_date)
                if slot_gender:
                    sched.slot_gender = slot_gender

            # Verificar requisitos de saude (EMS, etc) para exibicao
            sched.requires_ems = "Eletroestimulacao" in sched.modality.name or "FES" in sched.modality.name or "Eletrolipo" in sched.modality.name
            
            if sched.requires_ems:
                from app.models.health import ScreeningType
                sched.ems_ok = current_user.has_valid_screening(ScreeningType.EMS)
            else:
                sched.ems_ok = True

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

    # Validar agendamento (Geral)
    can_book, error_msg = Booking.validate_booking(current_user, schedule, date, subscription)
    if not can_book:
        flash(error_msg, 'danger')
        return redirect(url_for('student.schedule', date=date_str))

    # Validar triagem de saúde (PAR-Q / EMS)
    can_access, screening_msg = current_user.can_access_modality(schedule.modality)
    if not can_access:
        flash(screening_msg, 'warning')
        if "PAR-Q" in screening_msg:
            return redirect(url_for('health.fill_parq'))
        elif "anamnese" in screening_msg:
            return redirect(url_for('health.fill_ems'))
        return redirect(url_for('student.dashboard'))


    # Validar restricao de genero para modalidades segregadas
    if schedule.modality.requires_gender_segregation:
        can_book_gender, gender_msg = GenderDistributionService.can_user_book_slot(
            current_user, schedule.id, date
        )
        if not can_book_gender:
            flash(gender_msg, 'danger')
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

    # Buscar horas de cancelamento configuradas
    from app.models.system_config import SystemConfig
    cancellation_hours = SystemConfig.get_int('cancellation_hours', 2)

    # Verificar se pode cancelar
    if not booking.can_cancel:
        flash(f'Nao e possivel cancelar com menos de {cancellation_hours} horas de antecedencia.', 'danger')
        return redirect(url_for('student.my_bookings'))

    # Calcular penalidade de XP
    class_datetime = datetime.combine(booking.date, booking.schedule.start_time)
    time_until = class_datetime - datetime.now()
    xp_penalty = 0

    # Penalidade se cancelar muito proximo do limite
    penalty_threshold = timedelta(hours=cancellation_hours + 1)
    if time_until < penalty_threshold:
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
    from app.models.system_config import SystemConfig

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

    # Horas de cancelamento configuradas
    cancellation_hours = SystemConfig.get_int('cancellation_hours', 2)

    return render_template('student/my_bookings.html',
        upcoming=upcoming,
        past=past,
        cancellation_hours=cancellation_hours
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
    from app.models.system_config import SystemConfig

    recurring_bookings = RecurringBooking.query.filter_by(
        user_id=current_user.id
    ).order_by(RecurringBooking.is_active.desc(), RecurringBooking.created_at.desc()).all()

    cancellation_hours = SystemConfig.get_int('cancellation_hours', 2)

    return render_template('student/recurring_list.html',
        recurring_bookings=recurring_bookings,
        cancellation_hours=cancellation_hours
    )


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


@student_bp.route('/subscription/<int:id>/cancel-recurring', methods=['POST'])
@login_required
def cancel_recurring_subscription(id):
    """Cancelar cobranca recorrente NuPay"""
    subscription = Subscription.query.get_or_404(id)

    if subscription.user_id != current_user.id:
        abort(403)

    if not subscription.is_recurring:
        flash('Esta assinatura não possui cobrança recorrente ativa.', 'warning')
        return redirect(url_for('student.subscription_detail', id=id))

    try:
        from app.services.nupay import NuPayService
        nupay = NuPayService()
        
        # Cancelar na NuPay
        if subscription.nupay_subscription_id:
            nupay.cancel_subscription(subscription.nupay_subscription_id)
        
        # Atualizar no banco
        subscription.recurring_status = 'CANCELLED'
        subscription.is_recurring = False
        db.session.commit()
        
        flash('Cobrança recorrente cancelada com sucesso. Seus créditos atuais permanecem válidos até o vencimento.', 'success')
    except Exception as e:
        flash(f'Erro ao cancelar recorrência na NuPay: {str(e)}', 'danger')

    return redirect(url_for('student.subscription_detail', id=id))


@student_bp.route('/update-cpf', methods=['POST'])
@login_required
def update_cpf():
    """Atualizar CPF via AJAX"""
    data = request.get_json()
    if not data or 'cpf' not in data:
        return {'success': False, 'error': 'CPF não informado.'}, 400

    cpf = data.get('cpf')

    if not User.validate_cpf(cpf):
        return {'success': False, 'error': 'CPF inválido.'}, 400

    try:
        current_user.cpf = User.format_cpf(cpf)
        db.session.commit()
        return {'success': True}
    except Exception as e:
        return {'success': False, 'error': 'Erro ao salvar CPF.'}, 500


# ==================== XP E CREDITOS ====================

@student_bp.route('/xp-credits')
@login_required
def xp_credits():
    """Pagina de XP e Creditos - Conversao e Carteiras"""

    # Resumo completo do usuario
    summary = CreditService.get_user_summary(current_user.id)

    # Regras de conversao disponiveis
    available_rules = CreditService.get_available_rules(current_user.id)

    # Carteiras de credito ativas
    wallets = CreditWallet.get_user_active_wallets(current_user.id)

    # Creditos expirando em 7 dias
    expiring_wallets = CreditWallet.get_expiring_soon(current_user.id, days=7)

    return render_template('student/xp_credits.html',
        summary=summary,
        available_rules=available_rules,
        wallets=wallets,
        expiring_wallets=expiring_wallets
    )


@student_bp.route('/convert-xp/<int:rule_id>', methods=['POST'])
@login_required
def convert_xp(rule_id):
    """Executar conversao de XP em creditos"""

    result = CreditService.convert_xp(current_user.id, rule_id, is_automatic=False)

    if result['success']:
        conversion = result['conversion']
        wallet = result['wallet']
        flash(
            f'Conversao realizada! Voce ganhou {conversion.credits_granted} creditos '
            f'(validos ate {wallet.expires_at.strftime("%d/%m/%Y")}).',
            'success'
        )
    else:
        flash(f'Erro na conversao: {result["error"]}', 'danger')

    return redirect(url_for('student.xp_credits'))


@student_bp.route('/api/credit-preview/<int:credits_needed>')
@login_required
def credit_preview(credits_needed):
    """API para preview de quais creditos serao usados"""

    preview = CreditService.preview_credit_usage(current_user.id, credits_needed)

    return jsonify(preview)


@student_bp.route('/api/xp-summary')
@login_required
def xp_summary_api():
    """API para obter resumo de XP e creditos"""

    summary = CreditService.get_user_summary(current_user.id)

    return jsonify(summary)
