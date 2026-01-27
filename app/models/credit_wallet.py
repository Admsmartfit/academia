# app/models/credit_wallet.py

from app import db
from datetime import datetime
import enum


class CreditSourceType(enum.Enum):
    PURCHASE = "purchase"      # Compra de pacote
    CONVERSION = "conversion"  # Conversao de XP
    BONUS = "bonus"            # Bonus promocional
    REFUND = "refund"          # Estorno


class CreditWallet(db.Model):
    """
    Carteira individual de creditos com data de expiracao.
    Cada carteira representa um lote de creditos de uma fonte especifica.
    O sistema usa FIFO (primeiro a vencer, primeiro a usar) para debitar.
    """
    __tablename__ = 'credit_wallets'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Creditos
    credits_initial = db.Column(db.Integer, nullable=False)  # Creditos iniciais
    credits_remaining = db.Column(db.Integer, nullable=False)  # Creditos restantes

    # Origem
    source_type = db.Column(db.Enum(CreditSourceType), nullable=False)
    source_id = db.Column(db.Integer, nullable=True)  # ID da compra, conversao, etc

    # Validade
    expires_at = db.Column(db.DateTime, nullable=False)
    is_expired = db.Column(db.Boolean, default=False)  # Cache para queries rapidas

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    used_at = db.Column(db.DateTime, nullable=True)  # Quando foi totalmente consumido

    # Relacionamentos
    user = db.relationship('User', backref=db.backref('credit_wallets', lazy='dynamic'))

    # Index para queries FIFO eficientes
    __table_args__ = (
        db.Index('ix_credit_wallet_fifo', 'user_id', 'is_expired', 'expires_at', 'created_at'),
    )

    @property
    def is_active(self):
        """Verifica se a carteira ainda tem creditos validos"""
        if self.is_expired:
            return False
        if self.credits_remaining <= 0:
            return False
        if datetime.utcnow() > self.expires_at:
            return False
        return True

    @property
    def days_until_expiry(self):
        """Dias ate a expiracao"""
        if self.is_expired:
            return 0
        delta = self.expires_at - datetime.utcnow()
        return max(0, delta.days)

    @property
    def source_description(self):
        """Descricao amigavel da origem"""
        descriptions = {
            CreditSourceType.PURCHASE: "Compra de pacote",
            CreditSourceType.CONVERSION: "Conversao de XP",
            CreditSourceType.BONUS: "Bonus",
            CreditSourceType.REFUND: "Estorno",
        }
        return descriptions.get(self.source_type, "Desconhecido")

    def use_credits(self, amount):
        """
        Debita creditos desta carteira.
        Retorna a quantidade efetivamente debitada (pode ser menor se saldo insuficiente).
        """
        if not self.is_active:
            return 0

        debit = min(amount, self.credits_remaining)
        self.credits_remaining -= debit

        if self.credits_remaining == 0:
            self.used_at = datetime.utcnow()

        return debit

    def mark_expired(self):
        """Marca a carteira como expirada"""
        self.is_expired = True
        db.session.commit()

    @classmethod
    def get_user_active_wallets(cls, user_id, order_fifo=True):
        """
        Retorna carteiras ativas do usuario.
        Se order_fifo=True, ordena por data de expiracao (primeiro a vencer primeiro).
        """
        query = cls.query.filter(
            cls.user_id == user_id,
            cls.is_expired == False,
            cls.credits_remaining > 0,
            cls.expires_at > datetime.utcnow()
        )

        if order_fifo:
            query = query.order_by(cls.expires_at.asc(), cls.created_at.asc())

        return query.all()

    @classmethod
    def get_user_total_credits(cls, user_id):
        """Retorna total de creditos ativos do usuario"""
        result = db.session.query(
            db.func.coalesce(db.func.sum(cls.credits_remaining), 0)
        ).filter(
            cls.user_id == user_id,
            cls.is_expired == False,
            cls.credits_remaining > 0,
            cls.expires_at > datetime.utcnow()
        ).scalar()
        return int(result)

    @classmethod
    def get_expiring_soon(cls, user_id, days=7):
        """Retorna carteiras que vao expirar em X dias"""
        from datetime import timedelta
        threshold = datetime.utcnow() + timedelta(days=days)

        return cls.query.filter(
            cls.user_id == user_id,
            cls.is_expired == False,
            cls.credits_remaining > 0,
            cls.expires_at <= threshold,
            cls.expires_at > datetime.utcnow()
        ).order_by(cls.expires_at.asc()).all()

    def __repr__(self):
        return f'<CreditWallet {self.id}: {self.credits_remaining}/{self.credits_initial} (exp: {self.expires_at.date()})>'
