# app/models/conversion_rule.py

from app import db
from datetime import datetime


class ConversionRule(db.Model):
    """
    Regras de conversao de XP para creditos.
    Admin pode criar multiplas regras com diferentes taxas e condicoes.
    """
    __tablename__ = 'conversion_rules'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # Ex: "Bronze Reward"
    description = db.Column(db.String(255))  # Descricao para o usuario

    # Conversao
    xp_required = db.Column(db.Integer, nullable=False)  # XP necessario
    credits_granted = db.Column(db.Integer, nullable=False)  # Creditos concedidos
    credit_validity_days = db.Column(db.Integer, nullable=False, default=30)  # Validade em dias

    # Configuracoes
    is_active = db.Column(db.Boolean, default=True)
    is_automatic = db.Column(db.Boolean, default=False)  # Conversao automatica?

    # Limites
    max_uses_per_user = db.Column(db.Integer, nullable=True)  # Null = ilimitado
    cooldown_days = db.Column(db.Integer, nullable=True)  # Dias entre conversoes

    # Ordenacao/Prioridade
    priority = db.Column(db.Integer, default=0)  # Maior = mais prioritario

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamentos
    conversions = db.relationship('XPConversion', backref='rule', lazy='dynamic')

    @property
    def usage_count(self):
        """Total de vezes que esta regra foi usada"""
        return self.conversions.count()

    def get_user_usage_count(self, user_id):
        """Quantas vezes um usuario especifico usou esta regra"""
        from app.models.xp_conversion import XPConversion
        return XPConversion.query.filter_by(
            rule_id=self.id,
            user_id=user_id
        ).count()

    def get_user_last_conversion(self, user_id):
        """Ultima conversao de um usuario com esta regra"""
        from app.models.xp_conversion import XPConversion
        return XPConversion.query.filter_by(
            rule_id=self.id,
            user_id=user_id
        ).order_by(XPConversion.converted_at.desc()).first()

    def is_available_for_user(self, user_id, user_available_xp):
        """Verifica se a regra esta disponivel para o usuario"""
        if not self.is_active:
            return False, "Regra inativa"

        if user_available_xp < self.xp_required:
            return False, f"XP insuficiente (necessario: {self.xp_required})"

        # Verifica limite de usos
        if self.max_uses_per_user:
            usage_count = self.get_user_usage_count(user_id)
            if usage_count >= self.max_uses_per_user:
                return False, f"Limite de usos atingido ({self.max_uses_per_user}x)"

        # Verifica cooldown
        if self.cooldown_days:
            last_conversion = self.get_user_last_conversion(user_id)
            if last_conversion:
                days_since = (datetime.utcnow() - last_conversion.converted_at).days
                if days_since < self.cooldown_days:
                    remaining = self.cooldown_days - days_since
                    return False, f"Aguarde {remaining} dia(s) para usar novamente"

        return True, "Disponivel"

    def __repr__(self):
        return f'<ConversionRule {self.name}: {self.xp_required} XP -> {self.credits_granted} creditos>'
