# app/models/xp_conversion.py

from app import db
from datetime import datetime


class XPConversion(db.Model):
    """
    Registro de conversao de XP em creditos.
    Mantem historico de todas as conversoes realizadas.
    """
    __tablename__ = 'xp_conversions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rule_id = db.Column(db.Integer, db.ForeignKey('conversion_rules.id'), nullable=False)

    # Valores da conversao
    xp_spent = db.Column(db.Integer, nullable=False)  # XP gasto nesta conversao
    credits_granted = db.Column(db.Integer, nullable=False)  # Creditos gerados

    # Wallet criada
    wallet_id = db.Column(db.Integer, db.ForeignKey('credit_wallets.id'), nullable=True)

    # Tipo de conversao
    is_automatic = db.Column(db.Boolean, default=False)  # Foi automatica?

    # Timestamp
    converted_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamentos
    user = db.relationship('User', backref=db.backref('xp_conversions', lazy='dynamic'))
    wallet = db.relationship('CreditWallet', backref='conversion')

    # Index para queries frequentes
    __table_args__ = (
        db.Index('ix_xp_conversion_user_date', 'user_id', 'converted_at'),
    )

    @classmethod
    def get_user_total_xp_spent(cls, user_id):
        """Total de XP gasto em conversoes por um usuario"""
        result = db.session.query(
            db.func.coalesce(db.func.sum(cls.xp_spent), 0)
        ).filter(cls.user_id == user_id).scalar()
        return int(result)

    @classmethod
    def get_user_conversions(cls, user_id, limit=10):
        """Ultimas conversoes de um usuario"""
        return cls.query.filter_by(user_id=user_id).order_by(
            cls.converted_at.desc()
        ).limit(limit).all()

    @classmethod
    def get_monthly_stats(cls, year=None, month=None):
        """Estatisticas de conversoes do mes"""
        from datetime import date
        if not year:
            year = date.today().year
        if not month:
            month = date.today().month

        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)

        results = db.session.query(
            db.func.count(cls.id).label('total_conversions'),
            db.func.sum(cls.xp_spent).label('total_xp_spent'),
            db.func.sum(cls.credits_granted).label('total_credits_granted'),
            db.func.count(db.func.distinct(cls.user_id)).label('unique_users')
        ).filter(
            cls.converted_at >= start_date,
            cls.converted_at < end_date
        ).first()

        return {
            'total_conversions': results.total_conversions or 0,
            'total_xp_spent': results.total_xp_spent or 0,
            'total_credits_granted': results.total_credits_granted or 0,
            'unique_users': results.unique_users or 0
        }

    def __repr__(self):
        return f'<XPConversion {self.id}: {self.xp_spent} XP -> {self.credits_granted} creditos>'
