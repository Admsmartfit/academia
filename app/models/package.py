# app/models/package.py

from app import db
from datetime import datetime


class Package(db.Model):
    """
    Pacotes de creditos configuraveis pelo admin
    """
    __tablename__ = 'packages'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    credits = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)

    # Parcelamento
    installments = db.Column(db.Integer, default=1)  # Quantas parcelas
    installment_price = db.Column(db.Numeric(10, 2))  # Preco por parcela

    # Validade
    validity_days = db.Column(db.Integer, nullable=False)  # Ex: 90 dias

    # Visual (E-commerce)
    photo_url = db.Column(db.String(255))
    color = db.Column(db.String(7), default='#FF6B35')
    is_featured = db.Column(db.Boolean, default=False)  # Destaque
    display_order = db.Column(db.Integer, default=0)
    badge = db.Column(db.String(50))  # Ex: "MAIS VENDIDO", "NOVO"

    # Beneficios extras
    extra_benefits = db.Column(db.JSON)  # Ex: ["Toalha gratis", "Garrafinha"]

    # Recorrência NuPay
    is_recurring = db.Column(db.Boolean, default=False)  # Se é pacote recorrente
    recurring_interval_days = db.Column(db.Integer, default=30)  # Intervalo entre cobranças

    # Gamificação
    welcome_xp_bonus = db.Column(db.Integer, default=0)  # Bônus XP na primeira compra

    # Status
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamentos
    subscriptions = db.relationship('Subscription', backref='package', lazy=True)

    @property
    def price_per_credit(self):
        return float(self.price) / self.credits

    @property
    def discount_percent(self):
        """Calcula desconto em relacao a um preco base (R$ 50/aula)"""
        base_price = 50.0
        discount = ((base_price - self.price_per_credit) / base_price) * 100
        return max(0, round(discount))

    def __repr__(self):
        return f'<Package {self.name}>'
