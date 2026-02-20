# app/models/student_note.py

from app import db
from datetime import datetime
import enum


class NoteType(enum.Enum):
    RESTRICTION = "restriction"   # Restricao fisica/medica
    PROGRESS = "progress"         # Observacao de progresso
    BEHAVIOR = "behavior"         # Comportamento
    GENERAL = "general"           # Geral


NOTE_TYPE_LABELS = {
    "restriction": "Restricao",
    "progress": "Progresso",
    "behavior": "Comportamento",
    "general": "Geral",
}

NOTE_TYPE_COLORS = {
    "restriction": "#dc3545",
    "progress": "#198754",
    "behavior": "#ffc107",
    "general": "#6c757d",
}


class StudentNote(db.Model):
    """Observacoes do instrutor sobre o aluno."""
    __tablename__ = 'student_notes'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    instructor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    note_type = db.Column(db.Enum(NoteType), default=NoteType.GENERAL)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamentos
    student = db.relationship('User', foreign_keys=[student_id], backref='student_notes')
    instructor = db.relationship('User', foreign_keys=[instructor_id], backref='notes_written')

    __table_args__ = (
        db.Index('ix_student_notes_student', 'student_id', 'created_at'),
    )

    @property
    def type_label(self):
        return NOTE_TYPE_LABELS.get(self.note_type.value, 'Geral')

    @property
    def type_color(self):
        return NOTE_TYPE_COLORS.get(self.note_type.value, '#6c757d')

    def __repr__(self):
        return f'<StudentNote student={self.student_id} type={self.note_type.value}>'
