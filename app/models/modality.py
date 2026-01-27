# app/models/modality.py

from app import db
from datetime import datetime


class Modality(db.Model):
    __tablename__ = 'modalities'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    color = db.Column(db.String(7), default='#FF6B35')
    icon = db.Column(db.String(50))  # Emoji ou FontAwesome
    is_active = db.Column(db.Boolean, default=True)
    credits_cost = db.Column(db.Integer, default=1, nullable=False)
    is_featured = db.Column(db.Boolean, default=False)  # Destaque na landing page

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    schedules = db.relationship('ClassSchedule', backref='modality', lazy=True)

    def __repr__(self):
        return f'<Modality {self.name}>'
