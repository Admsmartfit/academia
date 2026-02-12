# app/routes/api/training.py

import logging
from datetime import date, timedelta

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from app import db
from app.models.training import (
    Exercise, TrainingPlan, WorkoutSession, WorkoutExercise,
    MuscleGroup, TrainingGoal
)
from app.models.user import User

logger = logging.getLogger(__name__)

training_api_bp = Blueprint('training_api', __name__, url_prefix='/api/training')


@training_api_bp.route('/exercises/list', methods=['GET'])
@login_required
def list_exercises():
    """
    Lista exercicios disponiveis com filtros opcionais.

    Query params:
        muscle_group: filtrar por grupo muscular
        search: buscar por nome
        difficulty: filtrar por dificuldade
    """
    query = Exercise.query.filter_by(is_active=True)

    muscle_group = request.args.get('muscle_group')
    if muscle_group:
        try:
            mg = MuscleGroup(muscle_group.lower())
            query = query.filter_by(muscle_group=mg)
        except ValueError:
            pass

    search = request.args.get('search', '').strip()
    if search:
        query = query.filter(Exercise.name.ilike(f'%{search}%'))

    difficulty = request.args.get('difficulty')
    if difficulty:
        from app.models.training import DifficultyLevel
        try:
            dl = DifficultyLevel(difficulty.lower())
            query = query.filter_by(difficulty_level=dl)
        except ValueError:
            pass

    exercises = query.order_by(Exercise.muscle_group, Exercise.name).all()

    return jsonify([{
        'id': ex.id,
        'name': ex.name,
        'muscle_group': ex.muscle_group.value,
        'muscle_group_label': ex.muscle_group_label,
        'video_url': ex.video_url,
        'thumbnail_url': ex.thumbnail_url,
        'description': ex.description,
        'equipment_needed': ex.equipment_needed,
        'difficulty_level': ex.difficulty_level.value if ex.difficulty_level else None,
        'difficulty_label': ex.difficulty_label
    } for ex in exercises])


@training_api_bp.route('/users/search', methods=['GET'])
@login_required
def search_users():
    """
    Busca usuarios por nome (para autocomplete de aluno na prescricao).

    Query params:
        q: termo de busca (min 2 caracteres)
        role: filtrar por role (default: student)
    """
    q = request.args.get('q', '').strip()
    role = request.args.get('role', 'student')

    if len(q) < 2:
        return jsonify([])

    # Busca mais flexivel: divide por espacos e garante que todos os termos existam no nome
    words = q.split()
    query_filters = [User.name.ilike(f'%{word}%') for word in words]
    
    users = User.query.filter(
        *query_filters,
        User.role == role,
        User.is_active == True
    ).limit(15).all()

    return jsonify([{
        'id': u.id,
        'name': u.name,
        'email': u.email
    } for u in users])


@training_api_bp.route('/prescribe', methods=['POST'])
@login_required
def prescribe_training():
    """
    Cria nova prescricao de treino.

    Request JSON:
        {
            "user_id": int,
            "goal": "HYPERTROPHY" | "FAT_LOSS" | "STRENGTH" | "HEALTH" | "SPORT",
            "validity_days": int,
            "notes": str (optional),
            "sessions": [
                {
                    "name": str,
                    "day_of_week": int | null,
                    "exercises": [
                        {
                            "exercise_id": int,
                            "sets": int,
                            "reps": str,
                            "rest": int,
                            "weight": str (optional),
                            "notes": str (optional)
                        }
                    ]
                }
            ]
        }
    """
    if current_user.role not in ('instructor', 'admin'):
        return jsonify({'success': False, 'error': 'Apenas instrutores podem prescrever treinos'}), 403

    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'Dados nao fornecidos'}), 400

    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Aluno nao selecionado'}), 400

    student = User.query.get(user_id)
    if not student:
        return jsonify({'success': False, 'error': 'Aluno nao encontrado'}), 404

    sessions_data = data.get('sessions', [])
    if not sessions_data:
        return jsonify({'success': False, 'error': 'Adicione pelo menos uma sessao de treino'}), 400

    try:
        goal_str = data.get('goal', 'HEALTH').lower()
        goal = TrainingGoal(goal_str)
    except ValueError:
        goal = TrainingGoal.HEALTH

    validity_days = data.get('validity_days', 30)
    today = date.today()

    try:
        # Desativar planos anteriores do aluno
        TrainingPlan.query.filter_by(
            user_id=user_id,
            is_active=True
        ).update({'is_active': False})

        # Criar plano
        plan = TrainingPlan(
            user_id=user_id,
            instructor_id=current_user.id,
            goal=goal,
            valid_from=today,
            valid_until=today + timedelta(days=validity_days),
            is_active=True,
            notes=data.get('notes', '')
        )
        db.session.add(plan)
        db.session.flush()  # get plan.id

        # Criar sessoes e exercicios
        for idx, session_data in enumerate(sessions_data):
            session_name = session_data.get('name', f'Treino {chr(65 + idx)}')
            day_of_week = session_data.get('day_of_week')
            if day_of_week == '' or day_of_week is None:
                day_of_week = None
            else:
                day_of_week = int(day_of_week)

            session = WorkoutSession(
                training_plan_id=plan.id,
                name=session_name,
                day_of_week=day_of_week,
                order_in_plan=idx + 1,
                estimated_duration_minutes=session_data.get('duration')
            )
            db.session.add(session)
            db.session.flush()

            for ex_idx, ex_data in enumerate(session_data.get('exercises', [])):
                exercise_id = ex_data.get('exercise_id')
                if not exercise_id:
                    continue

                exercise = Exercise.query.get(exercise_id)
                if not exercise:
                    continue

                workout_ex = WorkoutExercise(
                    workout_session_id=session.id,
                    exercise_id=exercise_id,
                    sets=int(ex_data.get('sets', 3)),
                    reps_range=ex_data.get('reps', '10-12'),
                    rest_seconds=int(ex_data.get('rest', 60)),
                    weight_suggestion=ex_data.get('weight', ''),
                    order_in_session=ex_idx + 1,
                    instructor_notes=ex_data.get('notes', '')
                )
                db.session.add(workout_ex)

        db.session.commit()

        logger.info(f"Prescricao criada: plan {plan.id} para user {user_id} por instrutor {current_user.id}")

        return jsonify({
            'success': True,
            'plan_id': plan.id,
            'message': f'Prescricao criada com sucesso! {len(sessions_data)} sessao(oes).'
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao criar prescricao: {e}")
        return jsonify({'success': False, 'error': f'Erro ao salvar: {str(e)}'}), 500


@training_api_bp.route('/<int:plan_id>', methods=['GET'])
@login_required
def get_training_plan(plan_id):
    """Retorna detalhes de um plano de treino."""
    plan = TrainingPlan.query.get_or_404(plan_id)

    # Verificar permissao
    if current_user.role == 'student' and plan.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Nao autorizado'}), 403

    return jsonify({
        'id': plan.id,
        'user': {'id': plan.user.id, 'name': plan.user.name},
        'instructor': {'id': plan.instructor.id, 'name': plan.instructor.name},
        'goal': plan.goal.value,
        'goal_label': plan.goal_label,
        'valid_from': plan.valid_from.isoformat(),
        'valid_until': plan.valid_until.isoformat(),
        'is_active': plan.is_active,
        'is_valid': plan.is_valid,
        'notes': plan.notes,
        'sessions': [{
            'id': s.id,
            'name': s.name,
            'day_of_week': s.day_of_week,
            'order_in_plan': s.order_in_plan,
            'estimated_duration_minutes': s.estimated_duration_minutes,
            'exercises': [{
                'id': we.id,
                'exercise_id': we.exercise_id,
                'name': we.exercise.name,
                'muscle_group': we.exercise.muscle_group.value,
                'muscle_group_label': we.exercise.muscle_group_label,
                'video_url': we.exercise.video_url,
                'sets': we.sets,
                'reps': we.reps_range,
                'rest': we.rest_seconds,
                'weight': we.weight_suggestion,
                'notes': we.instructor_notes
            } for we in s.exercises]
        } for s in plan.workout_sessions]
    })


@training_api_bp.route('/session/<int:session_id>/exercises', methods=['GET'])
@login_required
def get_session_exercises(session_id):
    """Retorna exercicios de uma sessao de treino."""
    session = WorkoutSession.query.get_or_404(session_id)
    plan = session.training_plan

    # Verificar permissao
    if current_user.role == 'student' and plan.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Nao autorizado'}), 403

    return jsonify([{
        'id': we.id,
        'exercise_id': we.exercise_id,
        'name': we.exercise.name,
        'muscle_group': we.exercise.muscle_group.value,
        'muscle_group_label': we.exercise.muscle_group_label,
        'video_url': we.exercise.video_url,
        'description': we.exercise.description,
        'equipment_needed': we.exercise.equipment_needed,
        'sets': we.sets,
        'reps': we.reps_range,
        'rest': we.rest_seconds,
        'weight': we.weight_suggestion,
        'notes': we.instructor_notes
    } for we in session.exercises])


@training_api_bp.route('/<int:plan_id>', methods=['DELETE'])
@login_required
def delete_training_plan(plan_id):
    """Desativa um plano de treino."""
    if current_user.role not in ('instructor', 'admin'):
        return jsonify({'success': False, 'error': 'Nao autorizado'}), 403

    plan = TrainingPlan.query.get_or_404(plan_id)
    plan.is_active = False
    db.session.commit()

@training_api_bp.route('/templates/list', methods=['GET'])
@login_required
def list_templates():
    """Lista templates de treino disponiveis."""
    from app.models.training import TrainingTemplate
    
    goal = request.args.get('goal')
    query = TrainingTemplate.query.filter(
        db.or_(
            TrainingTemplate.instructor_id == current_user.id,
            TrainingTemplate.is_public == True
        )
    )
    
    if goal:
        try:
            from app.models.training import TrainingGoal
            target_goal = TrainingGoal(goal.lower())
            query = query.filter_by(goal=target_goal)
        except ValueError:
            pass
            
    templates = query.order_by(TrainingTemplate.name).all()
    
    return jsonify([{
        'id': t.id,
        'name': t.name,
        'description': t.description,
        'goal': t.goal.value,
        'goal_label': t.goal.name.title(), # Simplificado
        'instructor_name': t.instructor.name,
        'session_count': len(t.sessions)
    } for t in templates])


@training_api_bp.route('/templates/<int:template_id>', methods=['GET'])
@login_required
def get_template(template_id):
    """Retorna detalhes de um template."""
    from app.models.training import TrainingTemplate
    template = TrainingTemplate.query.get_or_404(template_id)
    
    return jsonify({
        'id': template.id,
        'name': template.name,
        'goal': template.goal.value,
        'sessions': [{
            'name': s.name,
            'exercises': [{
                'exercise_id': we.exercise_id,
                'name': we.exercise.name,
                'muscle_group_label': we.exercise.muscle_group_label,
                'sets': we.sets,
                'reps': we.reps_range,
                'rest': we.rest_seconds,
                'weight': we.weight_suggestion,
                'notes': we.notes
            } for we in s.exercises]
        } for s in template.sessions]
    })


@training_api_bp.route('/templates/save', methods=['POST'])
@login_required
def save_template():
    """Salva um novo template de treino."""
    if current_user.role not in ('instructor', 'admin'):
        return jsonify({'success': False, 'error': 'Acesso negado'}), 403
        
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({'success': False, 'error': 'Nome do template obrigatorio'}), 400
        
    from app.models.training import TrainingTemplate, TemplateSession, TemplateExercise, TrainingGoal
    
    try:
        template = TrainingTemplate(
            name=data['name'],
            description=data.get('description', ''),
            goal=TrainingGoal(data.get('goal', 'health').lower()),
            instructor_id=current_user.id,
            is_public=data.get('is_public', True)
        )
        db.session.add(template)
        db.session.flush()
        
        for s_idx, s_data in enumerate(data.get('sessions', [])):
            session = TemplateSession(
                template_id=template.id,
                name=s_data.get('name', f'Treino {chr(65+s_idx)}'),
                order_in_template=s_idx + 1
            )
            db.session.add(session)
            db.session.flush()
            
            for e_idx, e_data in enumerate(s_data.get('exercises', [])):
                exercise = TemplateExercise(
                    template_session_id=session.id,
                    exercise_id=e_data['exercise_id'],
                    sets=int(e_data.get('sets', 3)),
                    reps_range=e_data.get('reps', '10-12'),
                    rest_seconds=int(e_data.get('rest', 60)),
                    weight_suggestion=e_data.get('weight', ''),
                    order_in_session=e_idx + 1,
                    notes=e_data.get('notes', '')
                )
                db.session.add(exercise)
                
        db.session.commit()
        return jsonify({'success': True, 'message': 'Template salvo com sucesso!', 'id': template.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
