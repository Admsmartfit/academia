# app/models/user.py

from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import enum


class UserRole(enum.Enum):
    ADMIN = "admin"
    STUDENT = "student"
    INSTRUCTOR = "instructor"


class User(UserMixin, db.Model):
    """
    Modelo de usuario do sistema
    """
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    # Role
    role = db.Column(db.String(20), default='student')

    # Gamificacao
    xp = db.Column(db.Integer, default=0)
    level = db.Column(db.Integer, default=1)

    # Perfil
    photo_url = db.Column(db.String(255))

    # Status
    is_active = db.Column(db.Boolean, default=True)

    # Datas
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    def set_password(self, password):
        """Define a senha do usuario"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verifica a senha do usuario"""
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_student(self):
        return self.role == 'student'

    @property
    def is_instructor(self):
        return self.role == 'instructor'

    @property
    def active_subscription(self):
        """Retorna a assinatura ativa do usuario"""
        from app.models.subscription import Subscription, SubscriptionStatus
        return Subscription.query.filter_by(
            user_id=self.id,
            status=SubscriptionStatus.ACTIVE
        ).first()

    @property
    def total_credits(self):
        """Total de creditos disponiveis"""
        from app.models.subscription import Subscription, SubscriptionStatus
        subscriptions = Subscription.query.filter_by(
            user_id=self.id,
            status=SubscriptionStatus.ACTIVE
        ).all()
        return sum(s.credits_remaining for s in subscriptions)

    @property
    def completed_bookings_count(self):
        """Total de aulas completadas"""
        from app.models.booking import Booking, BookingStatus
        return Booking.query.filter_by(
            user_id=self.id,
            status=BookingStatus.COMPLETED
        ).count()

    def add_xp(self, amount):
        """Adiciona XP ao usuario"""
        self.xp += amount
        # Calcula novo nivel (cada 100 XP = 1 nivel)
        new_level = (self.xp // 100) + 1
        if new_level > self.level:
            self.level = new_level
        db.session.commit()

    def __repr__(self):
        return f'<User {self.name}>'
