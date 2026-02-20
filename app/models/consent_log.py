# app/models/consent_log.py

from app import db
from datetime import datetime
import enum


class ConsentType(enum.Enum):
    TERMS_OF_USE = "terms_of_use"
    PRIVACY_POLICY = "privacy_policy"
    DATA_PROCESSING = "data_processing"
    MARKETING = "marketing"
    IMAGE_USE = "image_use"

    @property
    def label(self):
        labels = {
            'terms_of_use': 'Termos de Uso',
            'privacy_policy': 'Politica de Privacidade',
            'data_processing': 'Processamento de Dados',
            'marketing': 'Comunicacoes de Marketing',
            'image_use': 'Uso de Imagem',
        }
        return labels.get(self.value, self.value)


class ConsentLog(db.Model):
    """Registro de consentimento LGPD."""
    __tablename__ = 'consent_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    consent_type = db.Column(db.Enum(ConsentType), nullable=False)
    accepted = db.Column(db.Boolean, default=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(300), nullable=True)
    version = db.Column(db.String(20), default='1.0')
    revoked_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='consent_logs')

    @property
    def is_active(self):
        return self.accepted and self.revoked_at is None

    def revoke(self):
        self.revoked_at = datetime.utcnow()
        self.accepted = False

    def __repr__(self):
        return f'<ConsentLog {self.id} user={self.user_id} type={self.consent_type.value}>'
