# app/models/booking.py

from app import db
from datetime import datetime, timedelta
import enum


class BookingStatus(enum.Enum):
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"


class Booking(db.Model):
    __tablename__ = 'bookings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscriptions.id'))
    schedule_id = db.Column(db.Integer, db.ForeignKey('class_schedules.id'), nullable=False)

    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.Enum(BookingStatus), default=BookingStatus.CONFIRMED)

    # Recorrencia
    is_recurring = db.Column(db.Boolean, default=False)
    recurring_booking_id = db.Column(db.Integer, db.ForeignKey('recurring_bookings.id'))

    # Check-in
    checkin_at = db.Column(db.DateTime)
    xp_earned = db.Column(db.Integer, default=0)
    cost_at_booking = db.Column(db.Integer, nullable=False, default=1)

    # Lembretes
    reminder_24h_sent = db.Column(db.Boolean, default=False)
    reminder_2h_sent = db.Column(db.Boolean, default=False)
    reminder_hydration_sent = db.Column(db.Boolean, default=False)

    # Cancelamento
    cancelled_at = db.Column(db.DateTime)
    cancellation_reason = db.Column(db.Text)
    
    # Notas / Observacoes (Checklist, etc)
    notes = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamentos
    user = db.relationship('User', backref='bookings')
    schedule = db.relationship('ClassSchedule', backref='bookings')
    recurring = db.relationship('RecurringBooking', backref='generated_bookings', foreign_keys=[recurring_booking_id])

    @property
    def can_cancel(self):
        """Verifica se pode cancelar (horas configuradas pelo admin)"""
        from app.models.system_config import SystemConfig
        cancellation_hours = SystemConfig.get_int('cancellation_hours', 2)
        class_datetime = datetime.combine(self.date, self.schedule.start_time)
        now = datetime.now()
        return (class_datetime - now) > timedelta(hours=cancellation_hours)

    @property
    def cancellation_deadline(self):
        """Retorna o horario limite para cancelamento"""
        from app.models.system_config import SystemConfig
        cancellation_hours = SystemConfig.get_int('cancellation_hours', 2)
        class_datetime = datetime.combine(self.date, self.schedule.start_time)
        return class_datetime - timedelta(hours=cancellation_hours)

    def cancel(self, reason=None):
        """Cancela agendamento"""
        from app.models.system_config import SystemConfig
        cancellation_hours = SystemConfig.get_int('cancellation_hours', 2)
        if not self.can_cancel:
            raise ValueError(f"Nao e possivel cancelar com menos de {cancellation_hours}h de antecedencia")

        self.status = BookingStatus.CANCELLED
        self.cancelled_at = datetime.utcnow()
        self.cancellation_reason = reason

        # Estornar credito
        if self.subscription:
            self.subscription.refund_credit(self.cost_at_booking)

        db.session.commit()

    def checkin(self):
        """Realiza check-in"""
        self.status = BookingStatus.COMPLETED
        self.checkin_at = datetime.utcnow()
        self.xp_earned = 10  # XP base

        # Adicionar XP ao usuario
        self.user.xp += self.xp_earned

        db.session.commit()

    @staticmethod
    def validate_booking(user, schedule, date, subscription=None):
        """
        Valida se o usuario pode fazer o agendamento
        Retorna (sucesso, mensagem_erro)
        """
        from app.models.subscription import SubscriptionStatus

        # Verificar se tem assinatura ativa
        if subscription is None:
            subscription = user.active_subscription

        if subscription is None:
            return False, "Voce nao possui uma assinatura ativa."

        # Verificar se esta bloqueado
        if subscription.is_blocked:
            return False, "Sua assinatura esta bloqueada por inadimplencia."

        # Verificar se esta cancelada
        if subscription.is_cancelled:
            return False, "Sua assinatura foi cancelada."

        # Verificar creditos
        cost = schedule.modality.credits_cost
        if subscription.credits_remaining < cost:
            return False, f"Voce precisa de {cost} creditos. Disponivel: {subscription.credits_remaining}"

        # Verificar validade
        if subscription.days_until_expiry < 0:
            return False, "Sua assinatura expirou."

        # Verificar se a data esta dentro da validade
        if date > subscription.end_date:
            return False, f"Esta data esta fora da validade do seu pacote (ate {subscription.end_date.strftime('%d/%m/%Y')})."

        # Verificar se ja agendou a mesma aula
        duplicate = Booking.query.filter_by(
            user_id=user.id,
            schedule_id=schedule.id,
            date=date
        ).filter(
            Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.COMPLETED])
        ).first()

        if duplicate:
            return False, "Voce ja agendou esta aula."

        # Verificar conflito de horario
        existing = Booking.query.filter_by(
            user_id=user.id,
            date=date,
            status=BookingStatus.CONFIRMED
        ).join(Booking.schedule).filter(
            db.and_(
                Booking.schedule.has(start_time=schedule.start_time)
            )
        ).first()

        if existing:
            return False, "Voce ja possui um agendamento neste horario."

        # Verificar capacidade da aula
        bookings_count = Booking.query.filter_by(
            schedule_id=schedule.id,
            date=date,
            status=BookingStatus.CONFIRMED
        ).count()

        if bookings_count >= schedule.capacity:
            return False, "Esta aula esta lotada."

        return True, None

    def __repr__(self):
        return f'<Booking {self.id} - User {self.user_id} - {self.date}>'
