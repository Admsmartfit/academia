# app/models/payment.py

from app import db
from datetime import datetime
import enum


class PaymentStatusEnum(enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class Payment(db.Model):
    """
    Pagamento mensal de uma assinatura
    """
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscriptions.id'), nullable=False)

    # Parcela
    installment_number = db.Column(db.Integer, nullable=False)  # 1, 2, 3...
    installment_total = db.Column(db.Integer, nullable=False)   # Total de parcelas

    # Valores
    amount = db.Column(db.Numeric(10, 2), nullable=False)

    # Datas
    due_date = db.Column(db.Date, nullable=False)
    paid_date = db.Column(db.DateTime)

    # Status
    status = db.Column(db.Enum(PaymentStatusEnum), default=PaymentStatusEnum.PENDING)

    # Comprovante
    proof_url = db.Column(db.String(255))

    # Atraso
    overdue_days = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def is_overdue(self):
        if self.status == PaymentStatusEnum.PAID:
            return False
        return datetime.now().date() > self.due_date

    @property
    def days_overdue(self):
        if not self.is_overdue:
            return 0
        delta = datetime.now().date() - self.due_date
        return delta.days

    def mark_as_paid(self, proof_url=None):
        """Marca como pago"""
        self.status = PaymentStatusEnum.PAID
        self.paid_date = datetime.utcnow()
        if proof_url:
            self.proof_url = proof_url
        db.session.commit()

    def __repr__(self):
        return f'<Payment {self.installment_number}/{self.installment_total} - R$ {self.amount}>'
