# app/models/notification.py

from app import db
from datetime import datetime
import enum


class NotificationType(enum.Enum):
    CLASS_REMINDER = "class_reminder"       # Lembrete de aula
    CREDIT_EXPIRING = "credit_expiring"     # Credito expirando
    ACHIEVEMENT = "achievement"             # Conquista desbloqueada
    NEW_TRAINING = "new_training"           # Treino novo prescrito
    PAIN_RESPONSE = "pain_response"         # Resposta do instrutor
    GENERAL = "general"                     # Notificacao geral


NOTIFICATION_TYPE_LABELS = {
    "class_reminder": "Lembrete de Aula",
    "credit_expiring": "Credito Expirando",
    "achievement": "Conquista",
    "new_training": "Novo Treino",
    "pain_response": "Resposta do Instrutor",
    "general": "Aviso",
}

NOTIFICATION_TYPE_ICONS = {
    "class_reminder": "fas fa-calendar-check",
    "credit_expiring": "fas fa-exclamation-circle",
    "achievement": "fas fa-trophy",
    "new_training": "fas fa-dumbbell",
    "pain_response": "fas fa-comment-medical",
    "general": "fas fa-bell",
}


class Notification(db.Model):
    """Notificacoes internas do sistema para o aluno."""
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    notification_type = db.Column(db.Enum(NotificationType), default=NotificationType.GENERAL)
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=True)
    link = db.Column(db.String(300), nullable=True)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamentos
    user = db.relationship('User', backref=db.backref('notifications', lazy='dynamic'))

    __table_args__ = (
        db.Index('ix_notifications_user_read', 'user_id', 'is_read'),
    )

    @property
    def type_label(self):
        return NOTIFICATION_TYPE_LABELS.get(self.notification_type.value, 'Aviso')

    @property
    def type_icon(self):
        return NOTIFICATION_TYPE_ICONS.get(self.notification_type.value, 'fas fa-bell')

    @property
    def time_ago(self):
        """Retorna tempo relativo (ex: '2h atras')."""
        diff = datetime.utcnow() - self.created_at
        seconds = diff.total_seconds()
        if seconds < 60:
            return 'agora'
        elif seconds < 3600:
            return f'{int(seconds // 60)}min'
        elif seconds < 86400:
            return f'{int(seconds // 3600)}h'
        else:
            return f'{int(seconds // 86400)}d'

    @classmethod
    def get_unread_count(cls, user_id):
        return cls.query.filter_by(user_id=user_id, is_read=False).count()

    @classmethod
    def get_recent(cls, user_id, limit=20):
        return cls.query.filter_by(user_id=user_id).order_by(cls.created_at.desc()).limit(limit).all()

    @classmethod
    def create(cls, user_id, notification_type, title, message=None, link=None):
        n = cls(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            link=link
        )
        db.session.add(n)
        return n

    def __repr__(self):
        return f'<Notification {self.id} user={self.user_id} type={self.notification_type.value}>'
