# app/models/face_recognition.py

from app import db
from datetime import datetime


class FaceRecognitionLog(db.Model):
    """Log de tentativas de reconhecimento facial"""
    __tablename__ = 'face_recognition_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    confidence_score = db.Column(db.Float, nullable=False)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(200))
    success = db.Column(db.Boolean, default=True)
    error_message = db.Column(db.Text, nullable=True)

    # Relacionamento
    user = db.relationship('User', backref=db.backref('face_recognitions', lazy='dynamic'))

    def __repr__(self):
        return f'<FaceRecognitionLog user={self.user_id} success={self.success}>'
