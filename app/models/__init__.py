# app/models/__init__.py

from app.models.user import User
from app.models.package import Package
from app.models.subscription import Subscription, SubscriptionStatus, PaymentStatus
from app.models.payment import Payment, PaymentStatusEnum
from app.models.booking import Booking, BookingStatus
from app.models.recurring_booking import RecurringBooking, FrequencyType
from app.models.class_schedule import ClassSchedule
from app.models.modality import Modality
from app.models.achievement import Achievement, UserAchievement, CriteriaType
from app.models.whatsapp_template import WhatsAppTemplate, TemplateCategory, TemplateTrigger
from app.models.whatsapp_log import WhatsAppLog

__all__ = [
    'User',
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
    'Achievement',
    'UserAchievement',
    'CriteriaType',
    'WhatsAppTemplate',
    'TemplateCategory',
    'TemplateTrigger',
    'WhatsAppLog',
]
