# app/routes/admin/schedules.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import ClassSchedule, Modality, User, ScheduleSlotGender, Gender, Booking, BookingStatus
from app import db
from app.routes.admin.dashboard import admin_required
from app.services.gender_distribution_service import GenderDistributionService
from datetime import time, datetime, timedelta

schedules_bp = Blueprint('admin_schedules', __name__, url_prefix='/admin/schedules')

WEEKDAYS = [
    (0, 'Domingo'),
    (1, 'Segunda-feira'),
    (2, 'Terca-feira'),
    (3, 'Quarta-feira'),
    (4, 'Quinta-feira'),
    (5, 'Sexta-feira'),
    (6, 'Sabado')
]


@schedules_bp.route('/')
@login_required
@admin_required
def list_schedules():
    """Lista todos os horarios"""
    schedules = ClassSchedule.query.order_by(
        ClassSchedule.weekday,
        ClassSchedule.start_time
    ).all()

    # Agrupar por dia da semana
    schedules_by_day = {}
    for day_num, day_name in WEEKDAYS:
        schedules_by_day[day_name] = [s for s in schedules if s.weekday == day_num]

    return render_template('admin/schedules/list.html',
                         schedules_by_day=schedules_by_day,
                         weekdays=WEEKDAYS)


@schedules_bp.route('/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_schedule():
    """Criar novo horario (permite multiplos dias)"""
    if request.method == 'POST':
        # Converter horarios
        start_time = time.fromisoformat(request.form['start_time'])
        end_time = time.fromisoformat(request.form['end_time'])

        # Pegar multiplos dias selecionados
        weekdays_selected = request.form.getlist('weekdays')

        if not weekdays_selected:
            flash('Selecione pelo menos um dia da semana.', 'danger')
            return redirect(url_for('admin_schedules.create_schedule'))

        modality_id = int(request.form['modality_id'])
        instructor_id = int(request.form['instructor_id'])
        capacity = int(request.form['capacity'])

        # Criar um registro para cada dia selecionado
        created_count = 0
        for weekday in weekdays_selected:
            schedule = ClassSchedule(
                modality_id=modality_id,
                instructor_id=instructor_id,
                weekday=int(weekday),
                start_time=start_time,
                end_time=end_time,
                capacity=capacity,
                is_active=True
            )
            db.session.add(schedule)
            created_count += 1

        db.session.commit()

        if created_count == 1:
            flash('Horario criado com sucesso!', 'success')
        else:
            flash(f'{created_count} horarios criados com sucesso!', 'success')

        return redirect(url_for('admin_schedules.list_schedules'))

    modalities = Modality.query.filter_by(is_active=True).order_by(Modality.name).all()
    instructors = User.query.filter(
        User.role.in_(['instructor', 'admin']),
        User.is_active == True
    ).order_by(User.name).all()

    return render_template('admin/schedules/form.html',
                         schedule=None,
                         modalities=modalities,
                         instructors=instructors,
                         weekdays=WEEKDAYS)


@schedules_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_schedule(id):
    """Editar horario existente"""
    schedule = ClassSchedule.query.get_or_404(id)

    if request.method == 'POST':
        start_time = time.fromisoformat(request.form['start_time'])
        end_time = time.fromisoformat(request.form['end_time'])

        schedule.modality_id = int(request.form['modality_id'])
        schedule.instructor_id = int(request.form['instructor_id'])
        schedule.weekday = int(request.form['weekday'])
        schedule.start_time = start_time
        schedule.end_time = end_time
        schedule.capacity = int(request.form['capacity'])

        db.session.commit()

        flash('Horario atualizado!', 'success')
        return redirect(url_for('admin_schedules.list_schedules'))

    modalities = Modality.query.filter_by(is_active=True).order_by(Modality.name).all()
    instructors = User.query.filter(
        User.role.in_(['instructor', 'admin']),
        User.is_active == True
    ).order_by(User.name).all()

    return render_template('admin/schedules/form.html',
                         schedule=schedule,
                         modalities=modalities,
                         instructors=instructors,
                         weekdays=WEEKDAYS)


@schedules_bp.route('/toggle/<int:id>', methods=['POST'])
@login_required
@admin_required
def toggle_schedule(id):
    """Ativar/desativar horario"""
    schedule = ClassSchedule.query.get_or_404(id)
    schedule.is_active = not schedule.is_active
    db.session.commit()

    status = "ativado" if schedule.is_active else "desativado"
    flash(f'Horario {status}.', 'info')
    return redirect(url_for('admin_schedules.list_schedules'))


@schedules_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_schedule(id):
    """Deletar horario (se nao tiver agendamentos)"""
    schedule = ClassSchedule.query.get_or_404(id)

    if schedule.bookings:
        flash('Nao e possivel excluir este horario pois existem agendamentos associados.', 'danger')
        return redirect(url_for('admin_schedules.list_schedules'))

    db.session.delete(schedule)
    db.session.commit()

    flash('Horario excluido.', 'info')
    return redirect(url_for('admin_schedules.list_schedules'))


# ==================== GERENCIAMENTO DE GENERO ====================

@schedules_bp.route('/gender-management')
@login_required
@admin_required
def gender_management():
    """Gerenciamento de genero dos slots para modalidades segregadas"""
    # Data selecionada (hoje por padrao)
    date_str = request.args.get('date')
    if date_str:
        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = datetime.now().date()
    else:
        selected_date = datetime.now().date()

    # Buscar modalidades com segregacao por genero
    segregated_modalities = Modality.query.filter_by(
        requires_gender_segregation=True,
        is_active=True
    ).all()

    # Para cada modalidade, buscar slots do dia
    modality_slots = []
    for modality in segregated_modalities:
        # Dia da semana
        weekday = selected_date.weekday()
        sys_weekday = (weekday + 1) % 7

        schedules = ClassSchedule.query.filter_by(
            modality_id=modality.id,
            weekday=sys_weekday,
            is_active=True
        ).order_by(ClassSchedule.start_time).all()

        slots_info = []
        for sched in schedules:
            # Verificar genero atual do slot
            slot_gender_obj = ScheduleSlotGender.query.filter_by(
                schedule_id=sched.id,
                date=selected_date
            ).first()

            # Contar bookings do dia
            bookings_count = Booking.query.filter_by(
                schedule_id=sched.id,
                date=selected_date,
                status=BookingStatus.CONFIRMED
            ).count()

            slots_info.append({
                'schedule': sched,
                'slot_gender': slot_gender_obj,
                'bookings_count': bookings_count,
                'is_forced': slot_gender_obj.is_forced if slot_gender_obj else False
            })

        if schedules:
            modality_slots.append({
                'modality': modality,
                'slots': slots_info
            })

    # Estatisticas de genero
    gender_ratio = GenderDistributionService.get_gender_ratio()

    # Datas de navegacao
    prev_date = selected_date - timedelta(days=1)
    next_date = selected_date + timedelta(days=1)

    return render_template('admin/schedules/gender_management.html',
                         modality_slots=modality_slots,
                         selected_date=selected_date,
                         prev_date=prev_date,
                         next_date=next_date,
                         gender_ratio=gender_ratio,
                         Gender=Gender)


@schedules_bp.route('/force-gender/<int:schedule_id>', methods=['POST'])
@login_required
@admin_required
def force_gender(schedule_id):
    """Forca o genero de um slot especifico"""
    schedule = ClassSchedule.query.get_or_404(schedule_id)

    date_str = request.form.get('date')
    gender_str = request.form.get('gender')

    if not date_str or not gender_str:
        flash('Data e genero sao obrigatorios.', 'danger')
        return redirect(url_for('admin_schedules.gender_management'))

    try:
        slot_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        flash('Data invalida.', 'danger')
        return redirect(url_for('admin_schedules.gender_management'))

    # Converter genero
    if gender_str == 'male':
        gender = Gender.MALE
    elif gender_str == 'female':
        gender = Gender.FEMALE
    else:
        flash('Genero invalido.', 'danger')
        return redirect(url_for('admin_schedules.gender_management', date=date_str))

    # Verificar se ja existem agendamentos do sexo oposto
    existing_bookings = Booking.query.join(User).filter(
        Booking.schedule_id == schedule_id,
        Booking.date == slot_date,
        Booking.status == BookingStatus.CONFIRMED,
        User.gender.isnot(None),
        User.gender != gender
    ).count()

    if existing_bookings > 0:
        flash(f'Nao e possivel alterar o genero deste slot. Existem {existing_bookings} agendamento(s) do sexo oposto.', 'danger')
        return redirect(url_for('admin_schedules.gender_management', date=date_str))

    # Forcar genero
    ScheduleSlotGender.force_gender(
        schedule_id=schedule_id,
        slot_date=slot_date,
        gender=gender,
        forced_by_id=current_user.id
    )

    gender_label = 'Masculino' if gender == Gender.MALE else 'Feminino'
    flash(f'Slot das {schedule.start_time.strftime("%H:%M")} forcado para {gender_label}.', 'success')
    return redirect(url_for('admin_schedules.gender_management', date=date_str))


@schedules_bp.route('/apply-distribution/<int:modality_id>', methods=['POST'])
@login_required
@admin_required
def apply_distribution(modality_id):
    """Aplica a distribuicao automatica de genero para uma modalidade"""
    modality = Modality.query.get_or_404(modality_id)

    date_str = request.form.get('date')
    if not date_str:
        flash('Data e obrigatoria.', 'danger')
        return redirect(url_for('admin_schedules.gender_management'))

    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        flash('Data invalida.', 'danger')
        return redirect(url_for('admin_schedules.gender_management'))

    # Aplicar distribuicao (sem sobrescrever forcados)
    updated = GenderDistributionService.apply_distribution(modality_id, target_date, force=False)

    flash(f'Distribuicao aplicada para {modality.name}. {updated} slot(s) atualizado(s).', 'success')
    return redirect(url_for('admin_schedules.gender_management', date=date_str))


@schedules_bp.route('/clear-forced/<int:schedule_id>', methods=['POST'])
@login_required
@admin_required
def clear_forced(schedule_id):
    """Remove a definicao forcada de um slot"""
    schedule = ClassSchedule.query.get_or_404(schedule_id)

    date_str = request.form.get('date')
    if not date_str:
        flash('Data e obrigatoria.', 'danger')
        return redirect(url_for('admin_schedules.gender_management'))

    try:
        slot_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        flash('Data invalida.', 'danger')
        return redirect(url_for('admin_schedules.gender_management'))

    slot_gender = ScheduleSlotGender.query.filter_by(
        schedule_id=schedule_id,
        date=slot_date
    ).first()

    if slot_gender:
        slot_gender.is_forced = False
        slot_gender.forced_by_id = None
        slot_gender.forced_at = None
        db.session.commit()
        flash(f'Definicao forcada removida do slot das {schedule.start_time.strftime("%H:%M")}.', 'info')
    else:
        flash('Slot nao encontrado.', 'warning')

    return redirect(url_for('admin_schedules.gender_management', date=date_str))
