# app/models/xp_ledger.py

from app import db
from datetime import datetime, timedelta
import enum


class XPSourceType(enum.Enum):
    CLASS = "class"              # Aula completada
    ACHIEVEMENT = "achievement"  # Conquista desbloqueada
    BONUS = "bonus"              # Bonus promocional
    STREAK = "streak"            # Bonus por sequencia
    REFERRAL = "referral"        # Indicacao
    ADMIN = "admin"              # Ajuste manual do admin


class XPLedger(db.Model):
    """
    Registro granular de XP ganho.
    Permite rastrear quanto XP ja foi convertido vs disponivel.
    XP tem janela de 3 meses para conversao.
    """
    __tablename__ = 'xp_ledger'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # XP
    xp_amount = db.Column(db.Integer, nullable=False)  # Quantidade ganha

    # Origem
    source_type = db.Column(db.Enum(XPSourceType), nullable=False)
    source_id = db.Column(db.Integer, nullable=True)  # ID da aula, conquista, etc
    description = db.Column(db.String(255))  # Descricao amigavel

    # Datas
    earned_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)  # Janela de 3 meses

    # Conversao
    converted_amount = db.Column(db.Integer, default=0)  # Quanto ja foi convertido

    # Relacionamentos
    user = db.relationship('User', backref=db.backref('xp_ledger_entries', lazy='dynamic'))

    # Index para queries eficientes
    __table_args__ = (
        db.Index('ix_xp_ledger_user_available', 'user_id', 'expires_at', 'converted_amount'),
    )

    XP_WINDOW_MONTHS = 3  # Janela de conversao em meses

    @property
    def xp_available(self):
        """XP disponivel para conversao neste registro"""
        return self.xp_amount - self.converted_amount

    @property
    def is_expired(self):
        """Verifica se o XP saiu da janela de conversao"""
        return datetime.utcnow() > self.expires_at

    @property
    def is_fully_converted(self):
        """Verifica se todo XP deste registro ja foi convertido"""
        return self.converted_amount >= self.xp_amount

    @property
    def source_description(self):
        """Descricao amigavel da origem"""
        if self.description:
            return self.description
        descriptions = {
            XPSourceType.CLASS: "Aula completada",
            XPSourceType.ACHIEVEMENT: "Conquista",
            XPSourceType.BONUS: "Bonus",
            XPSourceType.STREAK: "Sequencia de treinos",
            XPSourceType.REFERRAL: "Indicacao",
            XPSourceType.ADMIN: "Ajuste administrativo",
        }
        return descriptions.get(self.source_type, "XP ganho")

    def use_for_conversion(self, amount):
        """
        Marca XP como usado para conversao.
        Retorna quantidade efetivamente marcada.
        """
        available = self.xp_available
        if available <= 0:
            return 0

        to_convert = min(amount, available)
        self.converted_amount += to_convert
        return to_convert

    @classmethod
    def create_entry(cls, user_id, xp_amount, source_type, source_id=None, description=None):
        """Cria um novo registro de XP com janela de expiracao automatica"""
        # Calcula data de expiracao (3 meses)
        expires_at = datetime.utcnow() + timedelta(days=cls.XP_WINDOW_MONTHS * 30)

        entry = cls(
            user_id=user_id,
            xp_amount=xp_amount,
            source_type=source_type,
            source_id=source_id,
            description=description,
            expires_at=expires_at
        )
        db.session.add(entry)
        return entry

    @classmethod
    def get_user_total_xp(cls, user_id):
        """XP total historico do usuario (para ranking)"""
        result = db.session.query(
            db.func.coalesce(db.func.sum(cls.xp_amount), 0)
        ).filter(cls.user_id == user_id).scalar()
        return int(result)

    @classmethod
    def get_user_available_xp(cls, user_id):
        """
        XP disponivel para conversao.
        Considera apenas XP dentro da janela de 3 meses que ainda nao foi convertido.
        """
        now = datetime.utcnow()
        result = db.session.query(
            db.func.coalesce(db.func.sum(cls.xp_amount - cls.converted_amount), 0)
        ).filter(
            cls.user_id == user_id,
            cls.expires_at > now,  # Dentro da janela
            cls.xp_amount > cls.converted_amount  # Ainda tem XP disponivel
        ).scalar()
        return int(result)

    @classmethod
    def get_user_converted_xp(cls, user_id):
        """Total de XP ja convertido em creditos"""
        result = db.session.query(
            db.func.coalesce(db.func.sum(cls.converted_amount), 0)
        ).filter(cls.user_id == user_id).scalar()
        return int(result)

    @classmethod
    def get_available_entries(cls, user_id):
        """
        Retorna entradas de XP disponiveis para conversao.
        Ordenadas por data de expiracao (primeiro a expirar primeiro).
        """
        now = datetime.utcnow()
        return cls.query.filter(
            cls.user_id == user_id,
            cls.expires_at > now,
            cls.xp_amount > cls.converted_amount
        ).order_by(cls.expires_at.asc()).all()

    @classmethod
    def consume_xp_for_conversion(cls, user_id, xp_needed):
        """
        Consome XP para conversao, usando FIFO (primeiro a expirar primeiro).
        Retorna True se conseguiu consumir todo o XP necessario.
        """
        entries = cls.get_available_entries(user_id)
        remaining = xp_needed

        for entry in entries:
            if remaining <= 0:
                break
            consumed = entry.use_for_conversion(remaining)
            remaining -= consumed

        return remaining == 0

    def __repr__(self):
        return f'<XPLedger {self.id}: +{self.xp_amount} XP ({self.source_type.value})>'
