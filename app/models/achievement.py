# app/models/achievement.py

from app import db
from datetime import datetime
import enum


class CriteriaType(enum.Enum):
    BOOKINGS_COUNT = "bookings_count"           # X aulas completadas
    STREAK_DAYS = "streak_days"                 # X dias consecutivos
    XP_THRESHOLD = "xp_threshold"               # Atingir X XP
    SPECIFIC_MODALITY = "specific_modality"     # X aulas de modalidade Y
    EARLY_MORNING = "early_morning"             # X aulas antes das 7h
    PURCHASE_COUNT = "purchase_count"           # X compras realizadas
    REFERRAL_COUNT = "referral_count"           # Indicar X amigos
    CUSTOM = "custom"                           # Logica custom


class Achievement(db.Model):
    """
    Conquistas configuraveis pelo admin
    """
    __tablename__ = 'achievements'

    id = db.Column(db.Integer, primary_key=True)

    # Informacoes basicas
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    icon_url = db.Column(db.String(255))  # Upload de emoji/imagem

    # Criterio
    criteria_type = db.Column(db.Enum(CriteriaType), nullable=False)
    criteria_value = db.Column(db.Integer, nullable=False)  # Ex: 10 aulas
    criteria_extra = db.Column(db.JSON)  # Dados extras (ex: modality_id)

    # Recompensa
    xp_reward = db.Column(db.Integer, default=0)

    # Visual
    color = db.Column(db.String(7), default='#FFD700')

    # Status
    is_active = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamentos
    unlocks = db.relationship('UserAchievement', backref='achievement', lazy=True)

    def __repr__(self):
        return f'<Achievement {self.name}>'


class UserAchievement(db.Model):
    """
    Conquistas desbloqueadas pelos usuarios
    """
    __tablename__ = 'user_achievements'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    achievement_id = db.Column(db.Integer, db.ForeignKey('achievements.id'), nullable=False)

    unlocked_at = db.Column(db.DateTime, default=datetime.utcnow)
    notified = db.Column(db.Boolean, default=False)  # WhatsApp enviado?

    user = db.relationship('User', backref='unlocked_achievements')

    def __repr__(self):
        return f'<UserAchievement User {self.user_id} - Achievement {self.achievement_id}>'
