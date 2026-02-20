# app/models/class_schedule.py

from app import db
from datetime import datetime, timedelta
from decimal import Decimal


class ClassSchedule(db.Model):
    __tablename__ = 'class_schedules'

    id = db.Column(db.Integer, primary_key=True)
    modality_id = db.Column(db.Integer, db.ForeignKey('modalities.id'), nullable=False)
    instructor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    weekday = db.Column(db.Integer, nullable=False)  # 0=Dom, 6=Sab
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    capacity = db.Column(db.Integer, default=10)

    # =========================================================================
    # Split Dinamico
    # =========================================================================
    # Taxa de split atual (% para colaborador) - calculado pelo algoritmo
    current_split_rate = db.Column(db.Numeric(5, 2), default=60.00)

    # Cache de ocupacao media (atualizado pelo job semanal)
    avg_occupancy_rate = db.Column(db.Numeric(5, 2), default=0.00)

    is_active = db.Column(db.Boolean, default=True)
    is_approved = db.Column(db.Boolean, default=True)  # Por padrao admin cria aprovado
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    instructor = db.relationship('User', foreign_keys=[instructor_id], backref='instructor_schedules')
    created_by = db.relationship('User', foreign_keys=[created_by_id], backref='created_schedules')

    @property
    def weekday_name(self):
        """Retorna o nome do dia da semana"""
        days = ['Domingo', 'Segunda', 'Terca', 'Quarta', 'Quinta', 'Sexta', 'Sabado']
        return days[self.weekday]

    def current_capacity(self, date=None):
        """Vagas ocupadas em uma data especifica"""
        from app.models.booking import Booking, BookingStatus

        if date is None:
            date = datetime.now().date()

        return Booking.query.filter_by(
            schedule_id=self.id,
            date=date,
            status=BookingStatus.CONFIRMED
        ).count()

    def available_spots(self, date=None):
        """Vagas disponiveis em uma data especifica"""
        return self.capacity - self.current_capacity(date)

    def calculate_occupancy_rate(self, days=30):
        """
        Calcula taxa de ocupacao media dos ultimos N dias.

        Retorna percentual de 0 a 100.
        """
        from app.models.booking import Booking, BookingStatus

        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)

        # Contar dias em que este horario ocorreu
        total_days = 0
        total_booked = 0
        total_capacity = 0

        current = start_date
        while current <= end_date:
            if current.weekday() == self.weekday:
                total_days += 1
                total_capacity += self.capacity

                # Contar bookings neste dia (CONFIRMED, COMPLETED, NO_SHOW)
                booked = Booking.query.filter(
                    Booking.schedule_id == self.id,
                    Booking.date == current,
                    Booking.status.in_([
                        BookingStatus.CONFIRMED,
                        BookingStatus.COMPLETED,
                        BookingStatus.NO_SHOW
                    ])
                ).count()
                total_booked += booked

            current += timedelta(days=1)

        if total_capacity == 0:
            return Decimal('0.00')

        rate = (Decimal(total_booked) / Decimal(total_capacity) * 100).quantize(Decimal('0.01'))
        return rate

    def __repr__(self):
        return f'<ClassSchedule {self.weekday_name} {self.start_time}>'
