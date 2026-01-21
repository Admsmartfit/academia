# app/models/class_schedule.py

from app import db
from datetime import datetime


class ClassSchedule(db.Model):
    __tablename__ = 'class_schedules'

    id = db.Column(db.Integer, primary_key=True)
    modality_id = db.Column(db.Integer, db.ForeignKey('modalities.id'), nullable=False)
    instructor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    weekday = db.Column(db.Integer, nullable=False)  # 0=Dom, 6=Sab
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    capacity = db.Column(db.Integer, default=10)

    is_active = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    instructor = db.relationship('User', foreign_keys=[instructor_id], backref='instructor_schedules')

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

    def __repr__(self):
        return f'<ClassSchedule {self.weekday_name} {self.start_time}>'
