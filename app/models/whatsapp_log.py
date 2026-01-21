# app/models/whatsapp_log.py

from app import db
from datetime import datetime
import enum


class MessageStatus(enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


class WhatsAppLog(db.Model):
    """
    Log de mensagens WhatsApp enviadas
    """
    __tablename__ = 'whatsapp_logs'

    id = db.Column(db.Integer, primary_key=True)

    # Usuario destinatario
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    phone = db.Column(db.String(20), nullable=False)

    # Template utilizado
    template_id = db.Column(db.Integer, db.ForeignKey('whatsapp_templates.id'))

    # Mensagem
    message_content = db.Column(db.Text, nullable=False)

    # Status
    status = db.Column(db.Enum(MessageStatus), default=MessageStatus.PENDING)
    megaapi_message_id = db.Column(db.String(100))

    # Erro (se houver)
    error_message = db.Column(db.Text)

    # Datas
    sent_at = db.Column(db.DateTime)
    delivered_at = db.Column(db.DateTime)
    read_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamentos
    user = db.relationship('User', backref='whatsapp_logs')
    template = db.relationship('WhatsAppTemplate', backref='logs')

    def mark_as_sent(self, message_id):
        """Marca como enviado"""
        self.status = MessageStatus.SENT
        self.megaapi_message_id = message_id
        self.sent_at = datetime.utcnow()
        db.session.commit()

    def mark_as_delivered(self):
        """Marca como entregue"""
        self.status = MessageStatus.DELIVERED
        self.delivered_at = datetime.utcnow()
        db.session.commit()

    def mark_as_read(self):
        """Marca como lido"""
        self.status = MessageStatus.READ
        self.read_at = datetime.utcnow()
        db.session.commit()

    def mark_as_failed(self, error):
        """Marca como falha"""
        self.status = MessageStatus.FAILED
        self.error_message = error
        db.session.commit()

    def __repr__(self):
        return f'<WhatsAppLog {self.id} - User {self.user_id}>'
