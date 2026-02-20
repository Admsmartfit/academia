# app/models/expense.py

from app import db
from datetime import datetime
import enum


class ExpenseCategory(enum.Enum):
    RENT = "rent"
    UTILITIES = "utilities"
    EQUIPMENT = "equipment"
    MAINTENANCE = "maintenance"
    CLEANING = "cleaning"
    MARKETING = "marketing"
    SOFTWARE = "software"
    INSURANCE = "insurance"
    TAXES = "taxes"
    SALARY = "salary"
    OTHER = "other"

    @property
    def label(self):
        labels = {
            'rent': 'Aluguel',
            'utilities': 'Agua/Luz/Internet',
            'equipment': 'Equipamentos',
            'maintenance': 'Manutencao',
            'cleaning': 'Limpeza',
            'marketing': 'Marketing',
            'software': 'Software/Sistemas',
            'insurance': 'Seguros',
            'taxes': 'Impostos',
            'salary': 'Salarios',
            'other': 'Outros',
        }
        return labels.get(self.value, self.value)


class Expense(db.Model):
    """Despesas da academia."""
    __tablename__ = 'expenses'

    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)
    category = db.Column(db.Enum(ExpenseCategory), default=ExpenseCategory.OTHER)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    is_recurring = db.Column(db.Boolean, default=False)
    recurring_day = db.Column(db.Integer, nullable=True)  # dia do mes para recorrentes
    notes = db.Column(db.Text, nullable=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    created_by = db.relationship('User', backref='expenses_created')

    @property
    def category_label(self):
        return self.category.label if self.category else 'Outros'

    @property
    def category_icon(self):
        icons = {
            'rent': 'fa-building',
            'utilities': 'fa-bolt',
            'equipment': 'fa-dumbbell',
            'maintenance': 'fa-wrench',
            'cleaning': 'fa-broom',
            'marketing': 'fa-bullhorn',
            'software': 'fa-laptop-code',
            'insurance': 'fa-shield-alt',
            'taxes': 'fa-file-invoice-dollar',
            'salary': 'fa-user-tie',
            'other': 'fa-receipt',
        }
        return icons.get(self.category.value, 'fa-receipt')

    def __repr__(self):
        return f'<Expense {self.id} {self.description} R${self.amount}>'
