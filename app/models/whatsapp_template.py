# app/models/whatsapp_template.py

from app import db
from datetime import datetime
import enum


class TemplateCategory(enum.Enum):
    TRANSACTIONAL = "transactional"  # Confirmacoes, lembretes
    MARKETING = "marketing"          # Promocoes


class TemplateTrigger(enum.Enum):
    PAYMENT_CONFIRMED = "payment_confirmed"
    CLASS_REMINDER_24H = "class_reminder_24h"
    CLASS_REMINDER_2H = "class_reminder_2h"
    CREDITS_EXPIRING = "credits_expiring"
    CREDITS_DEPLETED = "credits_depleted"
    ACHIEVEMENT_UNLOCKED = "achievement_unlocked"
    PAYMENT_OVERDUE = "payment_overdue"
    SUBSCRIPTION_BLOCKED = "subscription_blocked"
    WELCOME = "welcome"
    CUSTOM = "custom"


class WhatsAppTemplate(db.Model):
    """
    Templates de WhatsApp editaveis pelo admin
    """
    __tablename__ = 'whatsapp_templates'

    id = db.Column(db.Integer, primary_key=True)

    # Identificacao
    name = db.Column(db.String(100), nullable=False)  # Nome interno
    template_code = db.Column(db.String(100), unique=True)  # Codigo na Megaapi

    # Categoria
    category = db.Column(db.Enum(TemplateCategory), nullable=False)
    trigger = db.Column(db.Enum(TemplateTrigger), nullable=False)

    # Conteudo
    content = db.Column(db.Text, nullable=False)
    variables = db.Column(db.JSON)  # Ex: ["{{nome}}", "{{data}}"]

    # Status Megaapi
    megaapi_status = db.Column(db.String(20))  # pending, approved, rejected
    megaapi_id = db.Column(db.String(100))

    # Controle
    is_active = db.Column(db.Boolean, default=True)
    send_count = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<WhatsAppTemplate {self.name}>'
