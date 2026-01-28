# app/models/schedule_slot_gender.py

from app import db
from app.models.user import Gender
from datetime import datetime, date


class ScheduleSlotGender(db.Model):
    """
    Define o sexo permitido para um slot de horário em uma data específica.
    Usado para modalidades com segregação por sexo (ex: FES/Eletroestimulação).
    """
    __tablename__ = 'schedule_slot_genders'

    id = db.Column(db.Integer, primary_key=True)
    schedule_id = db.Column(db.Integer, db.ForeignKey('class_schedules.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)

    # Sexo permitido para este slot
    gender = db.Column(db.Enum(Gender), nullable=False)

    # Se foi definido manualmente pelo admin/instrutor
    is_forced = db.Column(db.Boolean, default=False)
    forced_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    forced_at = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamentos
    schedule = db.relationship('ClassSchedule', backref='slot_genders')
    forced_by = db.relationship('User', foreign_keys=[forced_by_id])

    # Índice único para evitar duplicatas
    __table_args__ = (
        db.UniqueConstraint('schedule_id', 'date', name='unique_schedule_date_gender'),
    )

    @property
    def gender_label(self):
        if self.gender == Gender.MALE:
            return 'Masculino'
        elif self.gender == Gender.FEMALE:
            return 'Feminino'
        return 'Indefinido'

    @classmethod
    def get_or_create(cls, schedule_id, slot_date, gender=None, is_forced=False, forced_by_id=None):
        """
        Obtém ou cria um slot de gênero.
        Se o slot já existe e is_forced=False, não sobrescreve um slot forçado.
        """
        existing = cls.query.filter_by(
            schedule_id=schedule_id,
            date=slot_date
        ).first()

        if existing:
            # Se já existe e é forçado, só atualiza se o novo também for forçado
            if existing.is_forced and not is_forced:
                return existing

            # Atualiza
            if gender:
                existing.gender = gender
            if is_forced:
                existing.is_forced = True
                existing.forced_by_id = forced_by_id
                existing.forced_at = datetime.utcnow()

            db.session.commit()
            return existing

        # Cria novo
        slot = cls(
            schedule_id=schedule_id,
            date=slot_date,
            gender=gender,
            is_forced=is_forced,
            forced_by_id=forced_by_id,
            forced_at=datetime.utcnow() if is_forced else None
        )
        db.session.add(slot)
        db.session.commit()
        return slot

    @classmethod
    def get_slot_gender(cls, schedule_id, slot_date):
        """
        Retorna o gênero definido para um slot, ou None se não definido.
        """
        slot = cls.query.filter_by(
            schedule_id=schedule_id,
            date=slot_date
        ).first()
        return slot.gender if slot else None

    @classmethod
    def force_gender(cls, schedule_id, slot_date, gender, forced_by_id):
        """
        Força o gênero de um slot manualmente.
        """
        return cls.get_or_create(
            schedule_id=schedule_id,
            slot_date=slot_date,
            gender=gender,
            is_forced=True,
            forced_by_id=forced_by_id
        )

    def __repr__(self):
        return f'<ScheduleSlotGender {self.schedule_id} {self.date} {self.gender_label}>'
