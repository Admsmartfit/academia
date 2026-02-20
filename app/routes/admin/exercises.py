from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models.training import Exercise, MuscleGroup, DifficultyLevel
from app.routes.admin.dashboard import admin_required
from app import db

exercises_bp = Blueprint('admin_exercises', __name__, url_prefix='/admin/exercises')


@exercises_bp.route('/')
@login_required
@admin_required
def list_exercises():
    """Lista todos os exercicios com filtros"""
    muscle = request.args.get('muscle_group', '')
    difficulty = request.args.get('difficulty', '')
    search = request.args.get('search', '')

    query = Exercise.query

    if muscle:
        try:
            query = query.filter(Exercise.muscle_group == MuscleGroup(muscle))
        except ValueError:
            pass

    if difficulty:
        try:
            query = query.filter(Exercise.difficulty_level == DifficultyLevel(difficulty))
        except ValueError:
            pass

    if search:
        query = query.filter(Exercise.name.ilike(f'%{search}%'))

    exercises = query.order_by(Exercise.name).all()

    return render_template(
        'admin/exercises/list.html',
        exercises=exercises,
        muscle_groups=MuscleGroup,
        difficulty_levels=DifficultyLevel,
        current_muscle=muscle,
        current_difficulty=difficulty,
        current_search=search
    )


@exercises_bp.route('/new', methods=['GET', 'POST'])
@login_required
@admin_required
def create_exercise():
    """Cria um exercicio manualmente"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            flash('Nome do exercicio e obrigatorio.', 'warning')
            return redirect(url_for('admin_exercises.create_exercise'))

        if Exercise.query.filter_by(name=name).first():
            flash('Ja existe um exercicio com esse nome.', 'warning')
            return redirect(url_for('admin_exercises.create_exercise'))

        try:
            new_ex = Exercise(
                name=name,
                muscle_group=MuscleGroup(request.form.get('muscle_group', 'full_body')),
                difficulty_level=DifficultyLevel(request.form.get('difficulty_level', 'beginner')),
                description=request.form.get('description', '').strip() or None,
                thumbnail_url=request.form.get('thumbnail_url', '').strip() or None,
                video_url=request.form.get('video_url', '').strip() or None,
                equipment_needed=request.form.get('equipment_needed', '').strip() or None,
                is_active=True,
                created_by_id=current_user.id
            )
            db.session.add(new_ex)
            db.session.commit()
            flash(f'Exercicio "{name}" criado com sucesso!', 'success')
            return redirect(url_for('admin_exercises.list_exercises'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar exercicio: {str(e)}', 'error')

    return render_template(
        'admin/exercises/form.html',
        exercise=None,
        muscle_groups=MuscleGroup,
        difficulty_levels=DifficultyLevel
    )


@exercises_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_exercise(id):
    """Edita um exercicio existente"""
    exercise = Exercise.query.get_or_404(id)

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            flash('Nome do exercicio e obrigatorio.', 'warning')
            return redirect(url_for('admin_exercises.edit_exercise', id=id))

        existing = Exercise.query.filter(Exercise.id != id, Exercise.name == name).first()
        if existing:
            flash('Ja existe outro exercicio com esse nome.', 'warning')
            return redirect(url_for('admin_exercises.edit_exercise', id=id))

        try:
            exercise.name = name
            exercise.muscle_group = MuscleGroup(request.form.get('muscle_group', 'full_body'))
            exercise.difficulty_level = DifficultyLevel(request.form.get('difficulty_level', 'beginner'))
            exercise.description = request.form.get('description', '').strip() or None
            exercise.thumbnail_url = request.form.get('thumbnail_url', '').strip() or None
            exercise.video_url = request.form.get('video_url', '').strip() or None
            exercise.equipment_needed = request.form.get('equipment_needed', '').strip() or None
            db.session.commit()
            flash(f'Exercicio "{name}" atualizado com sucesso!', 'success')
            return redirect(url_for('admin_exercises.list_exercises'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar exercicio: {str(e)}', 'error')

    return render_template(
        'admin/exercises/form.html',
        exercise=exercise,
        muscle_groups=MuscleGroup,
        difficulty_levels=DifficultyLevel
    )


@exercises_bp.route('/<int:id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_exercise(id):
    """Pausa ou ativa um exercicio"""
    exercise = Exercise.query.get_or_404(id)
    try:
        exercise.is_active = not exercise.is_active
        db.session.commit()
        status = 'ativado' if exercise.is_active else 'pausado'
        flash(f'Exercicio {status} com sucesso.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao alterar status do exercicio: {str(e)}', 'error')

    return redirect(url_for('admin_exercises.list_exercises'))


@exercises_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_exercise(id):
    """Exclui um exercicio (se nao estiver em uso)"""
    exercise = Exercise.query.get_or_404(id)
    try:
        db.session.delete(exercise)
        db.session.commit()
        flash('Exercicio excluido com sucesso.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Nao foi possivel excluir o exercicio. Ele pode estar vinculado a treinos existentes.', 'error')

    return redirect(url_for('admin_exercises.list_exercises'))
