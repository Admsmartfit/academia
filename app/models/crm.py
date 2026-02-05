# app/models/crm.py

from app import db
from datetime import datetime, date, timedelta
from sqlalchemy import func
import enum


class LeadSource(enum.Enum):
    WEBSITE = "website"
    INSTAGRAM = "instagram"
    REFERRAL = "referral"
    WALK_IN = "walk_in"
    GOOGLE_ADS = "google_ads"


class LeadStatus(enum.Enum):
    NEW = "new"
    CONTACTED = "contacted"
    VISITED = "visited"
    TRIAL = "trial"
    PROPOSAL = "proposal"
    WON = "won"
    LOST = "lost"


class RiskLevel(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Lead(db.Model):
    """Prospects antes de se tornarem alunos"""
    __tablename__ = 'leads'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    phone = db.Column(db.String(20), nullable=False, index=True)
    source = db.Column(db.Enum(LeadSource), default=LeadSource.WALK_IN)
    status = db.Column(db.Enum(LeadStatus), default=LeadStatus.NEW, index=True)
    interest_goal = db.Column(db.String(100), nullable=True)
    preferred_schedule = db.Column(db.String(100), nullable=True)
    budget_range = db.Column(db.String(50), nullable=True)

    # Tracking
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    last_contact_at = db.Column(db.DateTime, nullable=True)
    trial_class_date = db.Column(db.DateTime, nullable=True)
    converted_at = db.Column(db.DateTime, nullable=True)
    lost_reason = db.Column(db.String(200), nullable=True)

    # Atribuicao
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    # Se converter
    converted_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=True)

    # Relacionamentos
    assigned_to = db.relationship('User', foreign_keys=[assigned_to_id], backref='assigned_leads')
    converted_user = db.relationship('User', foreign_keys=[converted_user_id], backref='lead_origin')

    @property
    def source_label(self):
        labels = {
            LeadSource.WEBSITE: 'Website',
            LeadSource.INSTAGRAM: 'Instagram',
            LeadSource.REFERRAL: 'Indicacao',
            LeadSource.WALK_IN: 'Visita Presencial',
            LeadSource.GOOGLE_ADS: 'Google Ads',
        }
        return labels.get(self.source, str(self.source))

    @property
    def status_label(self):
        labels = {
            LeadStatus.NEW: 'Novo',
            LeadStatus.CONTACTED: 'Contactado',
            LeadStatus.VISITED: 'Visitou',
            LeadStatus.TRIAL: 'Aula Experimental',
            LeadStatus.PROPOSAL: 'Proposta Enviada',
            LeadStatus.WON: 'Convertido',
            LeadStatus.LOST: 'Perdido',
        }
        return labels.get(self.status, str(self.status))

    def __repr__(self):
        return f'<Lead {self.full_name} status={self.status}>'


class StudentHealthScore(db.Model):
    """Score de saude/retencao do aluno"""
    __tablename__ = 'student_health_scores'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    calculated_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # Componentes do score (0-100 cada)
    frequency_score = db.Column(db.Float, default=0)
    engagement_score = db.Column(db.Float, default=0)
    financial_score = db.Column(db.Float, default=0)
    tenure_score = db.Column(db.Float, default=0)

    # Score final
    total_score = db.Column(db.Float, nullable=False, index=True)
    risk_level = db.Column(db.Enum(RiskLevel), default=RiskLevel.LOW)

    # Flags de acao
    requires_attention = db.Column(db.Boolean, default=False, index=True)
    last_action_taken = db.Column(db.String(200), nullable=True)
    last_action_at = db.Column(db.DateTime, nullable=True)

    # Relacionamento
    user = db.relationship('User', backref=db.backref('health_scores', lazy='dynamic'))

    __table_args__ = (
        db.Index('ix_health_scores_user_date', 'user_id', 'calculated_at'),
    )

    @property
    def risk_label(self):
        labels = {
            RiskLevel.LOW: 'Saudavel',
            RiskLevel.MEDIUM: 'Em Risco',
            RiskLevel.HIGH: 'Critico',
            RiskLevel.CRITICAL: 'Critico Urgente',
        }
        return labels.get(self.risk_level, str(self.risk_level))

    @property
    def risk_color(self):
        colors = {
            RiskLevel.LOW: 'success',
            RiskLevel.MEDIUM: 'warning',
            RiskLevel.HIGH: 'danger',
            RiskLevel.CRITICAL: 'dark',
        }
        return colors.get(self.risk_level, 'secondary')

    def __repr__(self):
        return f'<StudentHealthScore user={self.user_id} score={self.total_score}>'

    @staticmethod
    def calculate_health_score(user_id, days_lookback=30):
        """
        Calcula o health score de um aluno.

        Algoritmo:
        - Frequencia Semanal (peso 40%)
        - Engajamento (peso 30%)
        - Financeiro (peso 20%)
        - Historico/Tenure (peso 10%)

        Returns:
            dict com scores individuais e total
        """
        from app.models.user import User
        from app.models.booking import Booking, BookingStatus
        from app.models.subscription import Subscription, SubscriptionStatus

        user = User.query.get(user_id)
        if not user:
            return None

        cutoff_date = date.today() - timedelta(days=days_lookback)

        # 1. Frequencia (peso 40%)
        checkins = Booking.query.filter(
            Booking.user_id == user_id,
            Booking.status == BookingStatus.COMPLETED,
            Booking.date >= cutoff_date
        ).count()

        weeks = max(days_lookback / 7, 1)
        weekly_avg = checkins / weeks

        if weekly_avg >= 4:
            frequency_score = 40
        elif weekly_avg >= 3:
            frequency_score = 30
        elif weekly_avg >= 2:
            frequency_score = 20
        elif weekly_avg >= 1:
            frequency_score = 10
        else:
            frequency_score = 0

        # 2. Engajamento (peso 30%)
        engagement_score = 0

        # Check-ins recentes (ultimos 7 dias)
        recent_checkins = Booking.query.filter(
            Booking.user_id == user_id,
            Booking.status == BookingStatus.COMPLETED,
            Booking.date >= date.today() - timedelta(days=7)
        ).count()

        if recent_checkins > 0:
            engagement_score += 15

        # Tem treino ativo (verificar se tem plano)
        # Basico: se tem bookings futuros agendados
        future_bookings = Booking.query.filter(
            Booking.user_id == user_id,
            Booking.status == BookingStatus.CONFIRMED,
            Booking.date >= date.today()
        ).count()

        if future_bookings > 0:
            engagement_score += 10

        # Screening de saude atualizado
        from app.models.health import ScreeningType
        try:
            if user.has_valid_screening(ScreeningType.PARQ):
                engagement_score += 5
        except Exception:
            pass

        # 3. Financeiro (peso 20%)
        financial_score = 0
        active_sub = Subscription.query.filter_by(
            user_id=user_id,
            status=SubscriptionStatus.ACTIVE
        ).first()

        if active_sub:
            financial_score = 20
        else:
            # Verifica se tem assinatura expirada recente
            expired_sub = Subscription.query.filter_by(
                user_id=user_id,
                status=SubscriptionStatus.EXPIRED
            ).order_by(Subscription.end_date.desc()).first()

            if expired_sub and expired_sub.end_date:
                days_expired = (date.today() - expired_sub.end_date).days
                if days_expired <= 7:
                    financial_score = 10

        # 4. Tenure/Historico (peso 10%)
        tenure_score = 0
        if user.created_at:
            months_active = (datetime.utcnow() - user.created_at).days / 30
            if months_active >= 6:
                tenure_score = 10
            elif months_active >= 3:
                tenure_score = 5

        # Score total
        total_score = frequency_score + engagement_score + financial_score + tenure_score

        # Determinar nivel de risco
        if total_score >= 70:
            risk_level = RiskLevel.LOW
        elif total_score >= 40:
            risk_level = RiskLevel.MEDIUM
        elif total_score >= 20:
            risk_level = RiskLevel.HIGH
        else:
            risk_level = RiskLevel.CRITICAL

        requires_attention = risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)

        return {
            'frequency_score': frequency_score,
            'engagement_score': engagement_score,
            'financial_score': financial_score,
            'tenure_score': tenure_score,
            'total_score': total_score,
            'risk_level': risk_level,
            'requires_attention': requires_attention,
        }


class AutomationLog(db.Model):
    """Log de envio de automações de retenção"""
    __tablename__ = 'automation_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    automation_type = db.Column(db.String(50), nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    opened = db.Column(db.Boolean, default=False)
    clicked = db.Column(db.Boolean, default=False)

    # Relacionamento
    user = db.relationship('User', backref=db.backref('automation_logs', lazy='dynamic'))

    def __repr__(self):
        return f'<AutomationLog user={self.user_id} type={self.automation_type}>'
