# app/models/training.py

from app import db
from datetime import datetime
from sqlalchemy.orm import validates
import enum


MUSCLE_GROUP_LABELS = {
    "chest": "Peito",
    "back": "Costas",
    "legs": "Pernas",
    "shoulders": "Ombros",
    "arms": "Bracos",
    "core": "Core/Abdomen",
    "full_body": "Corpo Inteiro",
}

DIFFICULTY_LABELS = {
    "beginner": "Iniciante",
    "intermediate": "Intermediario",
    "advanced": "Avancado",
}

GOAL_LABELS = {
    "hypertrophy": "Hipertrofia",
    "fat_loss": "Emagrecimento",
    "strength": "Forca",
    "health": "Saude",
    "sport": "Esporte",
}


class MuscleGroup(enum.Enum):
    CHEST = "chest"
    BACK = "back"
    LEGS = "legs"
    SHOULDERS = "shoulders"
    ARMS = "arms"
    CORE = "core"
    FULL_BODY = "full_body"

    @property
    def label(self):
        return MUSCLE_GROUP_LABELS.get(self.value, self.value)


class DifficultyLevel(enum.Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

    @property
    def label(self):
        return DIFFICULTY_LABELS.get(self.value, self.value)


class TrainingGoal(enum.Enum):
    HYPERTROPHY = "hypertrophy"
    FAT_LOSS = "fat_loss"
    STRENGTH = "strength"
    HEALTH = "health"
    SPORT = "sport"

    @property
    def label(self):
        return GOAL_LABELS.get(self.value, self.value)


class Exercise(db.Model):
    """Catalogo de exercicios disponveis"""
    __tablename__ = 'exercises'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    muscle_group = db.Column(db.Enum(MuscleGroup), nullable=False)
    video_url = db.Column(db.String(300), nullable=True)
    thumbnail_url = db.Column(db.String(300), nullable=True)
    description = db.Column(db.Text, nullable=True)
    equipment_needed = db.Column(db.String(200), nullable=True)
    difficulty_level = db.Column(db.Enum(DifficultyLevel), default=DifficultyLevel.BEGINNER)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # Relacionamentos
    created_by = db.relationship('User', backref='created_exercises')

    @property
    def muscle_group_label(self):
        return self.muscle_group.label if self.muscle_group else ''

    @property
    def difficulty_label(self):
        return self.difficulty_level.label if self.difficulty_level else ''

    def __repr__(self):
        return f'<Exercise {self.name}>'


class TrainingPlan(db.Model):
    """Plano de treino geral do aluno"""
    __tablename__ = 'training_plans'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    instructor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    goal = db.Column(db.Enum(TrainingGoal), default=TrainingGoal.HEALTH)
    valid_from = db.Column(db.Date, nullable=False)
    valid_until = db.Column(db.Date, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamentos
    user = db.relationship('User', foreign_keys=[user_id], backref='training_plans')
    instructor = db.relationship('User', foreign_keys=[instructor_id], backref='plans_created')
    workout_sessions = db.relationship('WorkoutSession', backref='training_plan',
                                       cascade='all, delete-orphan',
                                       order_by='WorkoutSession.order_in_plan')

    __table_args__ = (
        db.Index('ix_training_plans_user_active', 'user_id', 'is_active'),
    )

    @property
    def goal_label(self):
        return self.goal.label if self.goal else ''

    @property
    def is_valid(self):
        from datetime import date
        today = date.today()
        return self.is_active and self.valid_from <= today <= self.valid_until

    @validates('valid_until')
    def validate_dates(self, key, value):
        if self.valid_from and value < self.valid_from:
            raise ValueError('Data final deve ser posterior a data inicial')
        return value

    def __repr__(self):
        return f'<TrainingPlan user={self.user_id} goal={self.goal}>'


class WorkoutSession(db.Model):
    """Sessao de treino (Treino A, B, C, etc)"""
    __tablename__ = 'workout_sessions'

    id = db.Column(db.Integer, primary_key=True)
    training_plan_id = db.Column(db.Integer, db.ForeignKey('training_plans.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)  # ex: "Treino A - Peito e Triceps"
    day_of_week = db.Column(db.Integer, nullable=True)  # None se for sistema ABC
    order_in_plan = db.Column(db.Integer, nullable=False, default=1)
    estimated_duration_minutes = db.Column(db.Integer, nullable=True)

    # Relacionamentos
    exercises = db.relationship('WorkoutExercise', backref='workout_session',
                                cascade='all, delete-orphan',
                                order_by='WorkoutExercise.order_in_session')

    def __repr__(self):
        return f'<WorkoutSession {self.name}>'


class WorkoutExercise(db.Model):
    """Exercicio dentro de uma sessao de treino"""
    __tablename__ = 'workout_exercises'

    id = db.Column(db.Integer, primary_key=True)
    workout_session_id = db.Column(db.Integer, db.ForeignKey('workout_sessions.id'), nullable=False)
    exercise_id = db.Column(db.Integer, db.ForeignKey('exercises.id'), nullable=False)
    sets = db.Column(db.Integer, nullable=False, default=3)
    reps_range = db.Column(db.String(20), nullable=True)  # "8-12", "maximo", "30 segundos"
    rest_seconds = db.Column(db.Integer, nullable=True, default=60)
    weight_suggestion = db.Column(db.String(50), nullable=True)  # "20kg", "aumentar 2kg"
    order_in_session = db.Column(db.Integer, nullable=False, default=1)
    instructor_notes = db.Column(db.Text, nullable=True)

    # Relacionamentos
    exercise = db.relationship('Exercise', backref='workout_usages')

    __table_args__ = (
        db.Index('ix_workout_exercises_session', 'workout_session_id', 'order_in_session'),
    )

    def __repr__(self):
        return f'<WorkoutExercise exercise={self.exercise_id} sets={self.sets}>'


class TrainingSession(db.Model):
    """Registro de visualizacao/realizacao de treino"""
    __tablename__ = 'training_sessions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    workout_session_id = db.Column(db.Integer, db.ForeignKey('workout_sessions.id'), nullable=True)
    viewed_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    # Relacionamentos
    user = db.relationship('User', foreign_keys=[user_id], backref='training_sessions')
    workout_session = db.relationship('WorkoutSession')

    def __repr__(self):
        return f'<TrainingSession user={self.user_id} viewed={self.viewed_at}>'


# =============================================================================
# MODELOS DE TEMPLATE (MODELOS DE TREINO)
# =============================================================================

class TrainingTemplate(db.Model):
    """Modelo de treino reutilizavel (Template)"""
    __tablename__ = 'training_templates'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    goal = db.Column(db.Enum(TrainingGoal), default=TrainingGoal.HEALTH)
    instructor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_public = db.Column(db.Boolean, default=True)  # Se outros instrutores podem ver
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamentos
    instructor = db.relationship('User', foreign_keys=[instructor_id], backref='templates_created')
    sessions = db.relationship('TemplateSession', backref='template',
                               cascade='all, delete-orphan',
                               order_by='TemplateSession.order_in_template')

    def __repr__(self):
        return f'<TrainingTemplate {self.name}>'


class TemplateSession(db.Model):
    """Sessao dentro de um template (Ex: Treino A)"""
    __tablename__ = 'template_sessions'

    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(db.Integer, db.ForeignKey('training_templates.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    order_in_template = db.Column(db.Integer, nullable=False, default=1)

    # Relacionamentos
    exercises = db.relationship('TemplateExercise', backref='session',
                                cascade='all, delete-orphan',
                                order_by='TemplateExercise.order_in_session')

    def __repr__(self):
        return f'<TemplateSession {self.name}>'


class TemplateExercise(db.Model):
    """Exercicio dentro de uma sessao de template"""
    __tablename__ = 'template_exercises'

    id = db.Column(db.Integer, primary_key=True)
    template_session_id = db.Column(db.Integer, db.ForeignKey('template_sessions.id'), nullable=False)
    exercise_id = db.Column(db.Integer, db.ForeignKey('exercises.id'), nullable=False)
    sets = db.Column(db.Integer, nullable=False, default=3)
    reps_range = db.Column(db.String(20), nullable=True, default='10-12')
    rest_seconds = db.Column(db.Integer, nullable=True, default=60)
    weight_suggestion = db.Column(db.String(50), nullable=True)
    order_in_session = db.Column(db.Integer, nullable=False, default=1)
    notes = db.Column(db.Text, nullable=True)

    # Relacionamentos
    exercise = db.relationship('Exercise')

    def __repr__(self):
        return f'<TemplateExercise ex={self.exercise_id} sets={self.sets}>'
