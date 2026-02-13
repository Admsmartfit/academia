from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required
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


@exercises_bp.route('/import', methods=['GET', 'POST'])
@login_required
@admin_required
def import_exercises():
    """Importa exercicios da API Wger (Preview e Execucao)"""
    from app.services import wger_service
    
    if request.method == 'POST':
        # Recebe IDs selecionados
        selected_ids = request.form.getlist('exercise_ids')
        if not selected_ids:
            flash('Nenhum exercicio selecionado para importacao.', 'warning')
            return redirect(url_for('admin_exercises.import_exercises'))
            
        try:
            count = wger_service.import_selected_exercises(selected_ids)
            flash(f'{count} novos exercicios importados com sucesso!', 'success')
            return redirect(url_for('admin_exercises.list_exercises'))
        except Exception as e:
            flash(f'Erro ao importar exercicios selecionados: {str(e)}', 'error')
            return redirect(url_for('admin_exercises.import_exercises'))
    
    # GET: Mostra preview
    try:
        preview_exercises = wger_service.get_api_exercises_preview()
        return render_template(
            'admin/exercises/import_preview.html',
            exercises=preview_exercises,
            muscle_groups=MuscleGroup
        )
    except Exception as e:
        flash(f'Erro ao carregar preview da API: {str(e)}', 'error')
        return redirect(url_for('admin_exercises.list_exercises'))


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
