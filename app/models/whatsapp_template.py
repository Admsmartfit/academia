# app/models/whatsapp_template.py

from app import db
from datetime import datetime
import enum


class TemplateCategory(enum.Enum):
    TRANSACTIONAL = "Transacional (Alertas/Avisos)"
    MARKETING = "Marketing (Promoções)"


class TemplateTrigger(enum.Enum):
    PAYMENT_CONFIRMED = "Confirmação de Pagamento"
    CLASS_REMINDER_24H = "Lembrete de Aula (24h antes)"
    CLASS_REMINDER_2H = "Lembrete de Aula (2h antes)"
    CREDITS_EXPIRING = "Créditos com Baixa Validade"
    CREDITS_EXPIRING_1D = "Créditos Expiram Amanhã"
    CREDITS_EXPIRED = "Créditos Expiraram"
    CREDITS_DEPLETED = "Créditos Esgotados"
    ACHIEVEMENT_UNLOCKED = "Nova Conquista Desbloqueada"
    XP_CONVERSION_AUTO = "Conversão Automática de XP"
    XP_CONVERSION_MANUAL = "Conversão Manual de XP"
    XP_GOAL_NEAR = "XP Próximo de Meta"
    PAYMENT_OVERDUE = "Pagamento em Atraso"
    SUBSCRIPTION_BLOCKED = "Assinatura Bloqueada"
    SUBSCRIPTION_CANCELLED = "Assinatura Cancelada (Inadimplência)"
    WELCOME = "Boas-vindas (Novo Cadastro)"
    CUSTOM = "Personalizado / Envio Manual"


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
