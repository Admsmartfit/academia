# app/models/__init__.py

from app.models.user import User, Gender
from app.models.package import Package
from app.models.subscription import Subscription, SubscriptionStatus, PaymentStatus
from app.models.payment import Payment, PaymentStatusEnum
from app.models.booking import Booking, BookingStatus
from app.models.recurring_booking import RecurringBooking, FrequencyType
from app.models.class_schedule import ClassSchedule
from app.models.modality import Modality
from app.models.schedule_slot_gender import ScheduleSlotGender
from app.models.achievement import Achievement, UserAchievement, CriteriaType
from app.models.whatsapp_template import WhatsAppTemplate, TemplateCategory, TemplateTrigger
from app.models.whatsapp_log import WhatsAppLog
from app.models.system_config import SystemConfig

# XP to Credits Conversion System
from app.models.conversion_rule import ConversionRule
from app.models.credit_wallet import CreditWallet, CreditSourceType
from app.models.xp_conversion import XPConversion
from app.models.xp_ledger import XPLedger, XPSourceType

# Health Screening System
from app.models.health import HealthScreening, EMSSessionLog, ScreeningType, ScreeningStatus

# Face Recognition
from app.models.face_recognition import FaceRecognitionLog

# Training / Prescricao de Treino
from app.models.training import (
    Exercise, TrainingPlan, WorkoutSession, WorkoutExercise, TrainingSession,
    MuscleGroup, DifficultyLevel, TrainingGoal
)

# CRM e Retencao
from app.models.crm import (
    Lead, StudentHealthScore, AutomationLog,
    LeadSource, LeadStatus, RiskLevel
)

# Notificacoes
from app.models.notification import Notification, NotificationType

# Workout Logs e Observacoes
from app.models.workout_log import WorkoutLog
from app.models.student_note import StudentNote, NoteType

# Campanhas
from app.models.campaign import Campaign, CampaignStatus, CampaignTarget

# Despesas
from app.models.expense import Expense, ExpenseCategory

# LGPD e Auditoria
from app.models.consent_log import ConsentLog, ConsentType
from app.models.audit_log import AuditLog, AuditAction

# Split Bancario / Comissoes
from app.models.commission import (
    CommissionEntry, CommissionStatus,
    SplitConfiguration, SplitSettings,
    PayoutBatch, PayoutStatus,
    CollaboratorBankInfo, DemandLevel,
    ProfessionalType as CommissionProfessionalType
)

__all__ = [
    'User',
    'Gender',
    'Package',
    'Subscription',
    'SubscriptionStatus',
    'PaymentStatus',
    'Payment',
    'PaymentStatusEnum',
    'Booking',
    'BookingStatus',
    'RecurringBooking',
    'FrequencyType',
    'ClassSchedule',
    'Modality',
    'ScheduleSlotGender',
    'Achievement',
    'UserAchievement',
    'CriteriaType',
    'WhatsAppTemplate',
    'TemplateCategory',
    'TemplateTrigger',
    'WhatsAppLog',
    'SystemConfig',
    # XP to Credits Conversion
    'ConversionRule',
    'CreditWallet',
    'CreditSourceType',
    'XPConversion',
    'XPLedger',
    'XPSourceType',
    # Health Screening
    'HealthScreening',
    'EMSSessionLog',
    'ScreeningType',
    'ScreeningStatus',
    # Face Recognition
    'FaceRecognitionLog',
    # Training
    'Exercise',
    'TrainingPlan',
    'WorkoutSession',
    'WorkoutExercise',
    'TrainingSession',
    'MuscleGroup',
    'DifficultyLevel',
    'TrainingGoal',
    # CRM
    'Lead',
    'StudentHealthScore',
    'AutomationLog',
    'LeadSource',
    'LeadStatus',
    'RiskLevel',
    # Split Bancario / Comissoes
    'CommissionEntry',
    'CommissionStatus',
    'SplitConfiguration',
    'SplitSettings',
    'PayoutBatch',
    'PayoutStatus',
    'CollaboratorBankInfo',
    'DemandLevel',
    'CommissionProfessionalType',
    # Notificacoes
    'Notification',
    'NotificationType',
    # Workout Logs e Observacoes
    'WorkoutLog',
    'StudentNote',
    'NoteType',
    # Campanhas
    'Campaign',
    'CampaignStatus',
    'CampaignTarget',
    # Despesas
    'Expense',
    'ExpenseCategory',
    # LGPD e Auditoria
    'ConsentLog',
    'ConsentType',
    'AuditLog',
    'AuditAction',
]
