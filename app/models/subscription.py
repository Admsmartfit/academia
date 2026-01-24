# app/models/subscription.py

from app import db
from datetime import datetime, timedelta
from sqlalchemy import Enum
import enum


class SubscriptionStatus(enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"  # Atraso 15+ dias
    CANCELLED = "cancelled"  # Atraso 90+ dias
    EXPIRED = "expired"


class PaymentStatus(enum.Enum):
    PENDING = "pending"
    PARTIAL = "partial"  # Algumas parcelas pagas
    PAID = "paid"
    OVERDUE = "overdue"


class Subscription(db.Model):
    """
    Assinatura de um pacote por um usuario
    """
    __tablename__ = 'subscriptions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    package_id = db.Column(db.Integer, db.ForeignKey('packages.id'), nullable=False)

    # Creditos
    credits_total = db.Column(db.Integer, nullable=False)
    credits_used = db.Column(db.Integer, default=0)

    # Datas
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)

    # Status
    status = db.Column(db.Enum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE)
    payment_status = db.Column(db.Enum(PaymentStatus), default=PaymentStatus.PENDING)

    # Bloqueio
    blocked_at = db.Column(db.DateTime)
    block_reason = db.Column(db.String(255))

    # Recorrência NuPay
    is_recurring = db.Column(db.Boolean, default=False)  # Se é assinatura recorrente
    nupay_subscription_id = db.Column(db.String(100), nullable=True)  # ID da assinatura na NuPay
    recurring_status = db.Column(db.String(20), default='ACTIVE')  # ACTIVE, PAUSED, CANCELLED
    next_billing_date = db.Column(db.Date, nullable=True)  # Próxima cobrança
    last_billing_date = db.Column(db.Date, nullable=True)  # Última cobrança

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamentos
    user = db.relationship('User', backref='subscriptions')
    payments = db.relationship('Payment', backref='subscription', lazy=True, cascade='all, delete-orphan')
    bookings = db.relationship('Booking', backref='subscription', lazy=True)

    @property
    def credits_remaining(self):
        return self.credits_total - self.credits_used

    @property
    def is_blocked(self):
        return self.status == SubscriptionStatus.SUSPENDED

    @property
    def is_cancelled(self):
        return self.status == SubscriptionStatus.CANCELLED

    @property
    def days_until_expiry(self):
        if self.end_date:
            delta = self.end_date - datetime.now().date()
            return delta.days
        return 0

    @property
    def progress_percent(self):
        if self.credits_total == 0:
            return 0
        return round((self.credits_used / self.credits_total) * 100)

    def use_credit(self, amount=1):
        """Debita creditos"""
        if self.credits_remaining >= amount:
            self.credits_used += amount
            db.session.commit()
            return True
        return False

    def refund_credit(self, amount=1):
        """Estorna creditos (cancelamento)"""
        self.credits_used = max(0, self.credits_used - amount)
        db.session.commit()

    def block(self, reason):
        """Bloqueia a assinatura"""
        self.status = SubscriptionStatus.SUSPENDED
        self.blocked_at = datetime.utcnow()
        self.block_reason = reason
        db.session.commit()

    def unblock(self):
        """Desbloqueia a assinatura"""
        self.status = SubscriptionStatus.ACTIVE
        self.blocked_at = None
        self.block_reason = None
        db.session.commit()

    def cancel(self):
        """Cancela a assinatura (90 dias sem pagamento)"""
        self.status = SubscriptionStatus.CANCELLED
        self.credits_total = 0
        self.credits_used = 0
        db.session.commit()

    def __repr__(self):
        return f'<Subscription {self.id} - User {self.user_id}>'
