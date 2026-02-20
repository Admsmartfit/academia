# app/models/audit_log.py

from app import db
from datetime import datetime
import enum


class AuditAction(enum.Enum):
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    PAYMENT_APPROVED = "payment_approved"
    PAYMENT_REJECTED = "payment_rejected"
    SUBSCRIPTION_BLOCKED = "subscription_blocked"
    SUBSCRIPTION_CANCELLED = "subscription_cancelled"
    DATA_EXPORT = "data_export"
    DATA_ANONYMIZE = "data_anonymize"
    CONSENT_GIVEN = "consent_given"
    CONSENT_REVOKED = "consent_revoked"
    PASSWORD_CHANGE = "password_change"
    ROLE_CHANGE = "role_change"

    @property
    def label(self):
        labels = {
            'login': 'Login',
            'logout': 'Logout',
            'login_failed': 'Login Falhou',
            'create': 'Criacao',
            'update': 'Atualizacao',
            'delete': 'Exclusao',
            'payment_approved': 'Pagamento Aprovado',
            'payment_rejected': 'Pagamento Rejeitado',
            'subscription_blocked': 'Assinatura Bloqueada',
            'subscription_cancelled': 'Assinatura Cancelada',
            'data_export': 'Exportacao de Dados',
            'data_anonymize': 'Anonimizacao de Dados',
            'consent_given': 'Consentimento Dado',
            'consent_revoked': 'Consentimento Revogado',
            'password_change': 'Alteracao de Senha',
            'role_change': 'Alteracao de Perfil',
        }
        return labels.get(self.value, self.value)


class AuditLog(db.Model):
    """Log de auditoria para acoes criticas."""
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.Enum(AuditAction), nullable=False)
    entity_type = db.Column(db.String(50), nullable=True)  # 'User', 'Payment', etc.
    entity_id = db.Column(db.Integer, nullable=True)
    description = db.Column(db.String(500), nullable=True)
    old_value = db.Column(db.Text, nullable=True)
    new_value = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='audit_logs')

    @staticmethod
    def log(action, user_id=None, entity_type=None, entity_id=None,
            description=None, old_value=None, new_value=None, ip_address=None):
        """Registra uma acao de auditoria."""
        entry = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            description=description,
            old_value=old_value,
            new_value=new_value,
            ip_address=ip_address
        )
        db.session.add(entry)
        return entry

    @property
    def action_label(self):
        return self.action.label if self.action else '-'

    @property
    def action_color(self):
        colors = {
            'login': 'info',
            'logout': 'secondary',
            'login_failed': 'danger',
            'create': 'success',
            'update': 'primary',
            'delete': 'danger',
            'payment_approved': 'success',
            'payment_rejected': 'warning',
            'subscription_blocked': 'warning',
            'subscription_cancelled': 'danger',
            'data_export': 'info',
            'data_anonymize': 'danger',
            'consent_given': 'success',
            'consent_revoked': 'warning',
            'password_change': 'primary',
            'role_change': 'warning',
        }
        return colors.get(self.action.value, 'secondary')

    def __repr__(self):
        return f'<AuditLog {self.id} {self.action.value}>'
