# app/models/campaign.py

from app import db
from datetime import datetime
import enum


class CampaignStatus(enum.Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    SENDING = "sending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class CampaignTarget(enum.Enum):
    ALL_STUDENTS = "all_students"
    INACTIVE_30D = "inactive_30d"
    INACTIVE_60D = "inactive_60d"
    BIRTHDAYS = "birthdays"
    AT_RISK = "at_risk"
    NEW_STUDENTS = "new_students"
    CUSTOM = "custom"


CAMPAIGN_TARGET_LABELS = {
    "all_students": "Todos os Alunos",
    "inactive_30d": "Inativos 30+ dias",
    "inactive_60d": "Inativos 60+ dias",
    "birthdays": "Aniversariantes do Mes",
    "at_risk": "Alunos em Risco",
    "new_students": "Novos Alunos (30d)",
    "custom": "Selecao Manual",
}


class Campaign(db.Model):
    """Campanha de WhatsApp para envio em massa."""
    __tablename__ = 'campaigns'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    target = db.Column(db.Enum(CampaignTarget), default=CampaignTarget.ALL_STUDENTS)
    status = db.Column(db.Enum(CampaignStatus), default=CampaignStatus.DRAFT)
    scheduled_at = db.Column(db.DateTime, nullable=True)
    sent_at = db.Column(db.DateTime, nullable=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Metricas
    total_recipients = db.Column(db.Integer, default=0)
    total_sent = db.Column(db.Integer, default=0)
    total_delivered = db.Column(db.Integer, default=0)
    total_errors = db.Column(db.Integer, default=0)

    # Relacionamentos
    created_by = db.relationship('User', backref='campaigns_created')

    @property
    def target_label(self):
        return CAMPAIGN_TARGET_LABELS.get(self.target.value, self.target.value)

    @property
    def status_color(self):
        colors = {
            'draft': 'secondary',
            'scheduled': 'warning',
            'sending': 'info',
            'completed': 'success',
            'cancelled': 'danger',
        }
        return colors.get(self.status.value, 'secondary')

    def __repr__(self):
        return f'<Campaign {self.id} {self.name}>'
