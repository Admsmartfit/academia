# app/models/workout_log.py

from app import db
from datetime import datetime


class WorkoutLog(db.Model):
    """Registro de carga/performance do aluno por exercicio."""
    __tablename__ = 'workout_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    exercise_id = db.Column(db.Integer, db.ForeignKey('exercises.id'), nullable=False)
    instructor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    weight_kg = db.Column(db.Float, nullable=True)
    reps = db.Column(db.Integer, nullable=True)
    sets = db.Column(db.Integer, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    logged_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamentos
    user = db.relationship('User', foreign_keys=[user_id], backref='workout_logs')
    instructor = db.relationship('User', foreign_keys=[instructor_id])
    exercise = db.relationship('Exercise', backref='workout_logs')

    __table_args__ = (
        db.Index('ix_workout_logs_user_exercise', 'user_id', 'exercise_id', 'logged_at'),
    )

    def __repr__(self):
        return f'<WorkoutLog user={self.user_id} exercise={self.exercise_id} weight={self.weight_kg}>'
