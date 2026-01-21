# app/models/recurring_booking.py

from app import db
from datetime import datetime, timedelta
import enum


class FrequencyType(enum.Enum):
    WEEKLY = "weekly"          # Toda semana no mesmo dia/hora
    BIWEEKLY = "biweekly"      # A cada 2 semanas
    CUSTOM = "custom"          # Dias especificos da semana


class RecurringBooking(db.Model):
    """
    Configuracao de agendamento recorrente
    """
    __tablename__ = 'recurring_bookings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscriptions.id'), nullable=False)
    schedule_id = db.Column(db.Integer, db.ForeignKey('class_schedules.id'), nullable=False)

    # Frequencia
    frequency = db.Column(db.Enum(FrequencyType), default=FrequencyType.WEEKLY)
    custom_days = db.Column(db.JSON)  # Ex: [1, 3, 5] = Seg, Qua, Sex

    # Datas
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)  # Limite da assinatura
    next_occurrence = db.Column(db.Date)
    last_created = db.Column(db.Date)

    # Status
    is_active = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamentos
    user = db.relationship('User', backref='recurring_bookings')
    subscription = db.relationship('Subscription', backref='recurring_bookings')
    schedule = db.relationship('ClassSchedule', backref='recurring_bookings')

    def calculate_next_occurrence(self):
        """Calcula proxima data de agendamento"""
        if not self.last_created:
            return self.start_date

        if self.frequency == FrequencyType.WEEKLY:
            return self.last_created + timedelta(days=7)
        elif self.frequency == FrequencyType.BIWEEKLY:
            return self.last_created + timedelta(days=14)
        else:
            # Logica custom - para dias especificos
            return self.last_created + timedelta(days=7)

    def can_create_next(self):
        """Verifica se pode criar proximo agendamento"""
        if not self.is_active:
            return False, "Agendamento recorrente inativo"

        next_date = self.calculate_next_occurrence()

        if next_date > self.end_date:
            return False, "Data fora da validade da assinatura"

        cost = self.schedule.modality.credits_cost
        if self.subscription.credits_remaining < cost:
            return False, f"Voce precisa de {cost} creditos. Disponivel: {self.subscription.credits_remaining}"

        if self.subscription.is_blocked:
            return False, "Assinatura bloqueada"

        if self.subscription.is_cancelled:
            return False, "Assinatura cancelada"

        return True, None

    def create_next_booking(self):
        """Cria proximo agendamento automaticamente"""
        from app.models.booking import Booking, BookingStatus

        can_create, error = self.can_create_next()
        if not can_create:
            if "validade" in error or "inativo" in error:
                self.is_active = False
                db.session.commit()
            return None

        next_date = self.calculate_next_occurrence()

        # Verificar se ja existe um booking para esta data/horario
        existing = Booking.query.filter_by(
            user_id=self.user_id,
            schedule_id=self.schedule_id,
            date=next_date
        ).filter(
            Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.COMPLETED])
        ).first()

        if existing:
            # Ja existe, pular para proxima
            self.last_created = next_date
            self.next_occurrence = self.calculate_next_occurrence()
            db.session.commit()
            return None

        # Verificar capacidade
        bookings_count = Booking.query.filter_by(
            schedule_id=self.schedule_id,
            date=next_date,
            status=BookingStatus.CONFIRMED
        ).count()

        if bookings_count >= self.schedule.capacity:
            # Aula lotada, pular
            self.last_created = next_date
            self.next_occurrence = self.calculate_next_occurrence()
            db.session.commit()
            return None

        # Criar booking
        booking = Booking(
            user_id=self.user_id,
            subscription_id=self.subscription_id,
            schedule_id=self.schedule_id,
            date=next_date,
            status=BookingStatus.CONFIRMED,
            is_recurring=True,
            recurring_booking_id=self.id,
            cost_at_booking=self.schedule.modality.credits_cost
        )

        db.session.add(booking)
        self.last_created = next_date
        self.next_occurrence = self.calculate_next_occurrence()

        # Debitar credito
        self.subscription.credits_used += self.schedule.modality.credits_cost

        db.session.commit()

        return booking

    @staticmethod
    def process_all_recurring():
        """Processa todos os agendamentos recorrentes ativos"""
        today = datetime.now().date()
        created_count = 0

        recurring_list = RecurringBooking.query.filter_by(is_active=True).all()

        for recurring in recurring_list:
            # Processar ate 4 semanas a frente
            max_date = today + timedelta(days=28)

            while recurring.is_active and recurring.next_occurrence and recurring.next_occurrence <= max_date:
                booking = recurring.create_next_booking()
                if booking:
                    created_count += 1
                else:
                    break

        return created_count

    def __repr__(self):
        return f'<RecurringBooking {self.id} - User {self.user_id}>'
