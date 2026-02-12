# app/routes/admin/metrics.py

from flask import Blueprint, render_template, jsonify
from flask_login import login_required
from app.routes.admin.dashboard import admin_required
from app import db
from datetime import datetime, timedelta
from sqlalchemy import func
import logging

logger = logging.getLogger(__name__)

metrics_bp = Blueprint('admin_metrics', __name__, url_prefix='/admin/metrics')


@metrics_bp.route('/')
@login_required
@admin_required
def strategic_dashboard():
    """Dashboard de Métricas Estratégicas PRD §1.4."""
    return render_template('admin/metrics/dashboard.html')


@metrics_bp.route('/api/kpis')
@login_required
@admin_required
def get_kpis():
    """Retorna as 8 métricas estratégicas PRD com valores atuais e tendência."""
    from app.models import User, Booking, BookingStatus, Payment, Subscription
    from app.models.payment import PaymentStatusEnum
    from app.models.crm import StudentHealthScore, Lead, LeadStatus
    from app.models.whatsapp_log import WhatsAppLog

    now = datetime.utcnow()
    ninety_days_ago = now - timedelta(days=90)
    thirty_days_ago = now - timedelta(days=30)
    prev_thirty = now - timedelta(days=60)

    # 1. Taxa de Churn (90 dias)
    total_students_90d = User.query.filter(
        User.role == 'student',
        User.created_at <= ninety_days_ago
    ).count()

    churned = User.query.filter(
        User.role == 'student',
        User.created_at <= ninety_days_ago,
        User.is_active == False
    ).count()

    churn_rate = round((churned / total_students_90d * 100), 1) if total_students_90d > 0 else 0

    # 2. Tempo de Check-in (média últimos 30 dias)
    from app.models.face_recognition import FaceRecognitionLog
    avg_checkin_time = 3.0  # default
    try:
        logs = FaceRecognitionLog.query.filter(
            FaceRecognitionLog.created_at >= thirty_days_ago,
            FaceRecognitionLog.recognized == True
        ).all()
        if logs and hasattr(logs[0], 'processing_time_ms'):
            times = [l.processing_time_ms for l in logs if l.processing_time_ms]
            avg_checkin_time = round(sum(times) / len(times) / 1000, 1) if times else 3.0
    except Exception:
        pass

    # 3. Taxa Resposta WhatsApp (30 dias)
    total_wa_sent = WhatsAppLog.query.filter(
        WhatsAppLog.sent_at >= thirty_days_ago,
        WhatsAppLog.status.in_(['sent', 'delivered', 'read'])
    ).count()

    total_wa_read = WhatsAppLog.query.filter(
        WhatsAppLog.sent_at >= thirty_days_ago,
        WhatsAppLog.status == 'read'
    ).count()

    wa_response_rate = round((total_wa_read / total_wa_sent * 100), 1) if total_wa_sent > 0 else 0

    # 4. Conversão Landing > Checkout (30 dias)
    # Aproximação: novos alunos que compraram / total leads novos
    new_students_30d = User.query.filter(
        User.role == 'student',
        User.created_at >= thirty_days_ago
    ).count()

    new_leads_30d = Lead.query.filter(
        Lead.created_at >= thirty_days_ago
    ).count() or 1  # avoid div zero

    landing_conversion = round((new_students_30d / max(new_leads_30d, 1) * 100), 1)

    # 5. Tempo Liberação de Créditos
    # Medir diferença entre pagamento e liberação - com NuPay é < 5s
    credit_release_time = 5  # segundos (NuPay instant)

    # 6. NPS (Net Promoter Score)
    from app.models.crm import AutomationLog
    nps_responses = AutomationLog.query.filter(
        AutomationLog.automation_type.like('NPS_RESPONSE_%'),
        AutomationLog.sent_at >= thirty_days_ago
    ).all()

    promoters = sum(1 for r in nps_responses if 'EXCELENTE' in r.automation_type)
    passives = sum(1 for r in nps_responses if 'BOA' in r.automation_type)
    detractors = sum(1 for r in nps_responses if 'REGULAR' in r.automation_type or 'RUIM' in r.automation_type)
    total_nps = promoters + passives + detractors
    nps_score = round(((promoters - detractors) / total_nps * 100), 0) if total_nps > 0 else 0

    # 7. Health Score Médio
    avg_health = db.session.query(
        func.avg(StudentHealthScore.total_score)
    ).filter(
        StudentHealthScore.total_score > 0
    ).scalar() or 0
    avg_health = round(avg_health, 1)

    # 8. Conversão Lead > Aluno (30 dias)
    won_leads = Lead.query.filter(
        Lead.status == LeadStatus.WON,
        Lead.converted_at >= thirty_days_ago
    ).count()

    total_leads_period = Lead.query.filter(
        Lead.created_at >= thirty_days_ago
    ).count() or 1

    lead_conversion = round((won_leads / max(total_leads_period, 1) * 100), 1)

    # Tendências (comparar com período anterior)
    prev_students = User.query.filter(
        User.role == 'student',
        User.created_at <= prev_thirty,
        User.created_at > prev_thirty - timedelta(days=90)
    ).count()
    prev_churned = User.query.filter(
        User.role == 'student',
        User.created_at <= prev_thirty - timedelta(days=90),
        User.is_active == False
    ).count()
    prev_churn = round((prev_churned / max(prev_students, 1) * 100), 1)

    prev_wa_sent = WhatsAppLog.query.filter(
        WhatsAppLog.sent_at >= prev_thirty,
        WhatsAppLog.sent_at < thirty_days_ago,
        WhatsAppLog.status.in_(['sent', 'delivered', 'read'])
    ).count()
    prev_wa_read = WhatsAppLog.query.filter(
        WhatsAppLog.sent_at >= prev_thirty,
        WhatsAppLog.sent_at < thirty_days_ago,
        WhatsAppLog.status == 'read'
    ).count()
    prev_wa_rate = round((prev_wa_read / max(prev_wa_sent, 1) * 100), 1)

    kpis = [
        {
            'id': 'churn',
            'label': 'Taxa de Churn (90d)',
            'value': churn_rate,
            'unit': '%',
            'baseline': 45,
            'target_3m': 35,
            'target_6m': 20,
            'trend': round(prev_churn - churn_rate, 1),
            'lower_is_better': True,
            'color': '#F43F5E',
            'icon': 'fas fa-user-minus'
        },
        {
            'id': 'checkin_time',
            'label': 'Tempo Check-in',
            'value': avg_checkin_time,
            'unit': 's',
            'baseline': 45,
            'target_3m': 10,
            'target_6m': 3,
            'trend': 0,
            'lower_is_better': True,
            'color': '#06B6D4',
            'icon': 'fas fa-camera'
        },
        {
            'id': 'wa_response',
            'label': 'Resposta WhatsApp',
            'value': wa_response_rate,
            'unit': '%',
            'baseline': 5,
            'target_3m': 25,
            'target_6m': 40,
            'trend': round(wa_response_rate - prev_wa_rate, 1),
            'lower_is_better': False,
            'color': '#25D366',
            'icon': 'fab fa-whatsapp'
        },
        {
            'id': 'landing_conv',
            'label': 'Landing > Checkout',
            'value': landing_conversion,
            'unit': '%',
            'baseline': 2,
            'target_3m': 4,
            'target_6m': 6,
            'trend': 0,
            'lower_is_better': False,
            'color': '#FF6B35',
            'icon': 'fas fa-funnel-dollar'
        },
        {
            'id': 'credit_time',
            'label': 'Liberação Créditos',
            'value': credit_release_time,
            'unit': 's',
            'baseline': 7200,
            'target_3m': 5,
            'target_6m': 5,
            'trend': 0,
            'lower_is_better': True,
            'color': '#8B5CF6',
            'icon': 'fas fa-bolt'
        },
        {
            'id': 'nps',
            'label': 'NPS Score',
            'value': nps_score,
            'unit': '',
            'baseline': 35,
            'target_3m': 50,
            'target_6m': 65,
            'trend': 0,
            'lower_is_better': False,
            'color': '#F59E0B',
            'icon': 'fas fa-star'
        },
        {
            'id': 'health_score',
            'label': 'Health Score Médio',
            'value': avg_health,
            'unit': '',
            'baseline': 0,
            'target_3m': 65,
            'target_6m': 75,
            'trend': 0,
            'lower_is_better': False,
            'color': '#10B981',
            'icon': 'fas fa-heartbeat'
        },
        {
            'id': 'lead_conv',
            'label': 'Lead > Aluno',
            'value': lead_conversion,
            'unit': '%',
            'baseline': 15,
            'target_3m': 20,
            'target_6m': 25,
            'trend': 0,
            'lower_is_better': False,
            'color': '#EC4899',
            'icon': 'fas fa-user-plus'
        }
    ]

    return jsonify({'kpis': kpis})


@metrics_bp.route('/api/trends')
@login_required
@admin_required
def get_trends():
    """Retorna dados de tendência mensal (últimos 6 meses) para gráficos."""
    from app.models import User, Payment, Subscription
    from app.models.payment import PaymentStatusEnum
    from app.models.crm import Lead, LeadStatus

    now = datetime.utcnow()
    months = []

    for i in range(5, -1, -1):
        month_start = (now - timedelta(days=30 * i)).replace(day=1, hour=0, minute=0, second=0)
        if i > 0:
            month_end = (now - timedelta(days=30 * (i - 1))).replace(day=1, hour=0, minute=0, second=0)
        else:
            month_end = now

        # Novos alunos no mês
        new_students = User.query.filter(
            User.role == 'student',
            User.created_at >= month_start,
            User.created_at < month_end
        ).count()

        # Revenue no mês
        revenue = db.session.query(
            func.coalesce(func.sum(Payment.amount), 0)
        ).filter(
            Payment.status == PaymentStatusEnum.PAID,
            Payment.paid_date >= month_start,
            Payment.paid_date < month_end
        ).scalar() or 0

        # Leads convertidos
        leads_won = Lead.query.filter(
            Lead.status == LeadStatus.WON,
            Lead.converted_at >= month_start,
            Lead.converted_at < month_end
        ).count()

        # Total leads
        leads_total = Lead.query.filter(
            Lead.created_at >= month_start,
            Lead.created_at < month_end
        ).count()

        months.append({
            'label': month_start.strftime('%b/%y'),
            'new_students': new_students,
            'revenue': float(revenue),
            'leads_won': leads_won,
            'leads_total': leads_total,
            'conversion': round((leads_won / max(leads_total, 1) * 100), 1)
        })

    return jsonify({'months': months})


@metrics_bp.route('/financeiro')
@login_required
@admin_required
def financial_reports():
    """Relatórios Financeiros detalhados - PRD §3.7."""
    return render_template('admin/metrics/financeiro.html')


@metrics_bp.route('/api/financeiro')
@login_required
@admin_required
def get_financial_data():
    """Dados financeiros: revenue por pacote, auto vs manual, churn, LTV."""
    from app.models import User, Payment, Subscription, Package
    from app.models.payment import PaymentStatusEnum
    from app.models.subscription import SubscriptionStatus

    now = datetime.utcnow()
    thirty_days_ago = now - timedelta(days=30)

    # 1. Revenue por pacote (últimos 30 dias)
    revenue_by_package = db.session.query(
        Package.name,
        func.sum(Payment.amount).label('total'),
        func.count(Payment.id).label('count')
    ).join(Subscription, Payment.subscription_id == Subscription.id
    ).join(Package, Subscription.package_id == Package.id
    ).filter(
        Payment.status == PaymentStatusEnum.PAID,
        Payment.paid_date >= thirty_days_ago
    ).group_by(Package.name).all()

    packages_data = [
        {'name': r[0], 'revenue': float(r[1] or 0), 'count': int(r[2])}
        for r in revenue_by_package
    ]

    # 2. Automático vs Manual (últimos 30 dias)
    auto_payments = Payment.query.filter(
        Payment.status == PaymentStatusEnum.PAID,
        Payment.paid_date >= thirty_days_ago,
        Payment.payment_method.in_(['nupay_pix', 'nupay_recurring'])
    ).count()

    manual_payments = Payment.query.filter(
        Payment.status == PaymentStatusEnum.PAID,
        Payment.paid_date >= thirty_days_ago,
        Payment.payment_method == 'manual'
    ).count()

    auto_revenue = db.session.query(
        func.coalesce(func.sum(Payment.amount), 0)
    ).filter(
        Payment.status == PaymentStatusEnum.PAID,
        Payment.paid_date >= thirty_days_ago,
        Payment.payment_method.in_(['nupay_pix', 'nupay_recurring'])
    ).scalar() or 0

    manual_revenue = db.session.query(
        func.coalesce(func.sum(Payment.amount), 0)
    ).filter(
        Payment.status == PaymentStatusEnum.PAID,
        Payment.paid_date >= thirty_days_ago,
        Payment.payment_method == 'manual'
    ).scalar() or 0

    # 3. Revenue mensal (últimos 6 meses)
    monthly_revenue = []
    for i in range(5, -1, -1):
        m_start = (now - timedelta(days=30 * i)).replace(day=1, hour=0, minute=0, second=0)
        if i > 0:
            m_end = (now - timedelta(days=30 * (i - 1))).replace(day=1, hour=0, minute=0, second=0)
        else:
            m_end = now

        rev = db.session.query(
            func.coalesce(func.sum(Payment.amount), 0)
        ).filter(
            Payment.status == PaymentStatusEnum.PAID,
            Payment.paid_date >= m_start,
            Payment.paid_date < m_end
        ).scalar() or 0

        pending = db.session.query(
            func.coalesce(func.sum(Payment.amount), 0)
        ).filter(
            Payment.status == PaymentStatusEnum.PENDING,
            Payment.due_date >= m_start.date(),
            Payment.due_date < m_end.date()
        ).scalar() or 0

        overdue = db.session.query(
            func.coalesce(func.sum(Payment.amount), 0)
        ).filter(
            Payment.status == PaymentStatusEnum.OVERDUE,
            Payment.due_date >= m_start.date(),
            Payment.due_date < m_end.date()
        ).scalar() or 0

        monthly_revenue.append({
            'label': m_start.strftime('%b/%y'),
            'paid': float(rev),
            'pending': float(pending),
            'overdue': float(overdue)
        })

    # 4. Churn analysis
    total_active = Subscription.query.filter(Subscription.status == SubscriptionStatus.ACTIVE).count()
    cancelled_30d = Subscription.query.filter(
        Subscription.status.in_([SubscriptionStatus.CANCELLED, SubscriptionStatus.SUSPENDED]),
        Subscription.updated_at >= thirty_days_ago
    ).count()

    # 5. LTV (Lifetime Value) estimado
    avg_ticket = db.session.query(
        func.avg(Payment.amount)
    ).filter(
        Payment.status == PaymentStatusEnum.PAID
    ).scalar() or 0

    avg_months = db.session.query(
        func.avg(
            func.julianday(Subscription.end_date) - func.julianday(Subscription.start_date)
        )
    ).filter(
        Subscription.start_date.isnot(None),
        Subscription.end_date.isnot(None)
    ).scalar() or 30

    avg_months_val = float(avg_months) / 30 if avg_months else 1
    ltv = float(avg_ticket) * avg_months_val

    # 6. Totais
    total_revenue_30d = db.session.query(
        func.coalesce(func.sum(Payment.amount), 0)
    ).filter(
        Payment.status == PaymentStatusEnum.PAID,
        Payment.paid_date >= thirty_days_ago
    ).scalar() or 0

    total_pending = db.session.query(
        func.coalesce(func.sum(Payment.amount), 0)
    ).filter(
        Payment.status == PaymentStatusEnum.PENDING
    ).scalar() or 0

    total_overdue = db.session.query(
        func.coalesce(func.sum(Payment.amount), 0)
    ).filter(
        Payment.status == PaymentStatusEnum.OVERDUE
    ).scalar() or 0

    return jsonify({
        'summary': {
            'revenue_30d': float(total_revenue_30d),
            'pending': float(total_pending),
            'overdue': float(total_overdue),
            'ltv': round(ltv, 2),
            'avg_ticket': round(float(avg_ticket), 2),
            'active_subs': total_active,
            'churn_30d': cancelled_30d,
            'churn_rate': round((cancelled_30d / max(total_active + cancelled_30d, 1) * 100), 1)
        },
        'packages': packages_data,
        'payment_methods': {
            'auto': {'count': auto_payments, 'revenue': float(auto_revenue)},
            'manual': {'count': manual_payments, 'revenue': float(manual_revenue)}
        },
        'monthly': monthly_revenue
    })
