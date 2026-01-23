# app/routes/admin/schedules.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.models import ClassSchedule, Modality, User
from app import db
from app.routes.admin.dashboard import admin_required
from datetime import time

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
