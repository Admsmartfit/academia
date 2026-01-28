import enum
from datetime import datetime
from app import db

class ScreeningType(enum.Enum):
    PARQ = "parq"  # Musculação
    EMS = "ems"    # Eletroestimulação FES
    ELETROLIPO = "eletrolipo"  # Eletrolipólise

class ScreeningStatus(enum.Enum):
    APTO = "apto"
    PENDENTE_MEDICO = "pendente_medico"
    BLOQUEADO = "bloqueado"  # Contraindicação absoluta
    EXPIRADO = "expirado"

class HealthScreening(db.Model):
    __tablename__ = 'health_screenings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Tipo de questionário
    screening_type = db.Column(db.Enum(ScreeningType), nullable=False)
    
    # Respostas
    responses = db.Column(db.JSON, nullable=False)
    # Ex PAR-Q: {q1: false, q2: false, ..., q7: false}
    # Ex EMS: {q1: false, q2: false, ..., q9: false}
    
    # Status
    status = db.Column(db.Enum(ScreeningStatus), nullable=False)
    
    # Assinatura Digital
    acceptance_ip = db.Column(db.String(45), nullable=False)
    acceptance_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    accepted_terms = db.Column(db.Boolean, default=True)
    
    # Validade
    expires_at = db.Column(db.DateTime, nullable=False)
    # PAR-Q: +12 meses
    # EMS/Eletro: +6 meses
    
    # Atestado (se necessário)
    medical_certificate_url = db.Column(db.String(500))
    medical_certificate_uploaded_at = db.Column(db.DateTime)
    reminder_sent = db.Column(db.Boolean, default=False)
    
    # Aprovação manual
    approved_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    approved_at = db.Column(db.DateTime)
    approval_notes = db.Column(db.Text)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    
    # Relacionamentos
    user = db.relationship('User', foreign_keys=[user_id], backref='health_screenings')
    approved_by = db.relationship('User', foreign_keys=[approved_by_id])

class EMSSessionLog(db.Model):
    __tablename__ = 'ems_session_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    instructor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Tipo de procedimento
    procedure_type = db.Column(db.Enum(ScreeningType), nullable=False)  # EMS ou ELETROLIPO
    
    # Parâmetros
    frequency_hz = db.Column(db.Integer)  # Frequência em Hz
    intensity_ma = db.Column(db.Integer)  # Intensidade em mA
    duration_minutes = db.Column(db.Integer)  # Duração
    treatment_area = db.Column(db.String(100))  # Área tratada
    
    # Feedback
    discomfort_reported = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text)
    
    # Timestamps
    session_date = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    booking = db.relationship('Booking', backref='ems_logs')
    user = db.relationship('User', foreign_keys=[user_id])
    instructor = db.relationship('User', foreign_keys=[instructor_id])
