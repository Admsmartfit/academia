# app/routes/admin/dashboard.py

from flask import Blueprint, render_template, abort
from flask_login import login_required, current_user
from functools import wraps
from app.models import (
    User, Package, Subscription, Payment, Booking,
    ClassSchedule, SubscriptionStatus, PaymentStatusEnum, BookingStatus
)
from app import db
from sqlalchemy import func
from datetime import datetime, timedelta

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    """Decorator para proteger rotas admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/')
@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Dashboard principal do admin"""

    # Metricas gerais
    total_students = User.query.filter_by(role='student', is_active=True).count()
    active_subscriptions = Subscription.query.filter_by(status=SubscriptionStatus.ACTIVE).count()

    # Faturamento do mes
    start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_revenue = db.session.query(func.sum(Payment.amount)).filter(
        Payment.status == PaymentStatusEnum.PAID,
        Payment.paid_date >= start_of_month
    ).scalar() or 0

    # Pendencias
    pending_payments = Payment.query.filter_by(status=PaymentStatusEnum.PENDING).count()
    overdue_payments = Payment.query.filter_by(status=PaymentStatusEnum.OVERDUE).count()

    # Aulas hoje
    today = datetime.now().date()
    classes_today = ClassSchedule.query.filter_by(
        weekday=today.weekday(),
        is_active=True
    ).count()

    total_bookings_today = Booking.query.filter_by(
        date=today,
        status=BookingStatus.CONFIRMED
    ).count()

    # Taxa de ocupacao (semana)
    week_ago = datetime.now() - timedelta(days=7)
    total_capacity = db.session.query(func.sum(ClassSchedule.capacity)).scalar() or 1
    total_bookings = Booking.query.filter(
        Booking.date >= week_ago.date(),
        Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.COMPLETED])
    ).count()
    occupancy_rate = round((total_bookings / (total_capacity * 7)) * 100, 1) if total_capacity > 0 else 0

    # Novos alunos este mes
    new_students = User.query.filter(
        User.role == 'student',
        User.created_at >= start_of_month
    ).count()

    # Compras pendentes de aprovacao (com comprovante)
    pending_purchases = Payment.query.filter(
        Payment.status == PaymentStatusEnum.PENDING,
        Payment.proof_url != None
    ).order_by(Payment.created_at.desc()).limit(5).all()

    # Assinaturas expirando em 7 dias
    week_from_now = datetime.now().date() + timedelta(days=7)
    expiring_soon = Subscription.query.filter(
        Subscription.end_date <= week_from_now,
        Subscription.status == SubscriptionStatus.ACTIVE
    ).count()

    return render_template('admin/dashboard.html',
        total_students=total_students,
        active_subscriptions=active_subscriptions,
        monthly_revenue=monthly_revenue,
        pending_payments=pending_payments,
        overdue_payments=overdue_payments,
        classes_today=classes_today,
        total_bookings_today=total_bookings_today,
        occupancy_rate=occupancy_rate,
        new_students=new_students,
        pending_purchases=pending_purchases,
        expiring_soon=expiring_soon
    )
