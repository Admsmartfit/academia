# app/models/commission.py
"""
Modelos para o sistema de Split Bancario Dinamico e Gestao de Marketplace.

Este modulo implementa:
- CommissionEntry: Registro de cada transacao de comissao
- SplitConfiguration: Configuracao de split por horario/modalidade
- PayoutBatch: Lotes de pagamento para colaboradores
- CollaboratorBankInfo: Dados bancarios dos colaboradores
"""

import enum
from datetime import datetime, date
from decimal import Decimal

from app import db


class ProfessionalType(enum.Enum):
    """Tipo de profissional para regras de comissao."""
    INSTRUCTOR = 'instructor'      # Professor de aulas - recebe em No-Show
    TECHNICIAN = 'technician'      # Tecnica de estetica - recebe em No-Show
    NUTRITIONIST = 'nutritionist'  # Nutricionista - NAO recebe em No-Show


class CommissionStatus(enum.Enum):
    """Status da entrada de comissao."""
    PENDING = 'pending'        # Aguardando processamento
    APPROVED = 'approved'      # Aprovada para pagamento
    PAID = 'paid'              # Paga ao colaborador
    CANCELLED = 'cancelled'    # Cancelada (estorno, etc)


class PayoutStatus(enum.Enum):
    """Status do lote de pagamento."""
    DRAFT = 'draft'            # Rascunho, ainda em composicao
    PENDING = 'pending'        # Aguardando aprovacao do admin
    APPROVED = 'approved'      # Aprovado, aguardando pagamento
    PROCESSING = 'processing'  # Em processamento bancario
    PAID = 'paid'              # Pago com sucesso
    FAILED = 'failed'          # Falha no pagamento


class DemandLevel(enum.Enum):
    """Nivel de demanda para split dinamico."""
    LOW = 'low'        # < 40% ocupacao - Split 20/80 (academia/colaborador)
    STANDARD = 'standard'  # 40-80% ocupacao - Split 40/60
    HIGH = 'high'      # > 80% ocupacao - Split 60/40


# =============================================================================
# Dados Bancarios do Colaborador
# =============================================================================

class CollaboratorBankInfo(db.Model):
    """Dados bancarios do colaborador para recebimento de comissoes."""
    __tablename__ = 'collaborator_bank_info'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)

    # Dados bancarios
    bank_code = db.Column(db.String(10))  # Codigo do banco (ex: 001, 341)
    bank_name = db.Column(db.String(100))
    agency = db.Column(db.String(10))
    account_number = db.Column(db.String(20))
    account_type = db.Column(db.String(20))  # corrente, poupanca
    account_holder_name = db.Column(db.String(200))
    account_holder_cpf = db.Column(db.String(14))

    # PIX (alternativa)
    pix_key_type = db.Column(db.String(20))  # cpf, email, phone, random
    pix_key = db.Column(db.String(100))

    # Auditoria
    is_verified = db.Column(db.Boolean, default=False)
    verified_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamentos
    user = db.relationship('User', backref=db.backref('bank_info', uselist=False))

    def __repr__(self):
        return f'<CollaboratorBankInfo user={self.user_id}>'

    @property
    def has_bank_data(self):
        """Verifica se tem dados bancarios completos."""
        return bool(self.bank_code and self.agency and self.account_number)

    @property
    def has_pix(self):
        """Verifica se tem PIX cadastrado."""
        return bool(self.pix_key)

    @property
    def can_receive_payment(self):
        """Verifica se pode receber pagamento."""
        return self.has_bank_data or self.has_pix


# =============================================================================
# Configuracao de Split por Horario
# =============================================================================

class SplitConfiguration(db.Model):
    """
    Configuracao de split para um horario especifico.

    O split define quanto vai para a academia vs colaborador.
    Exemplo: academy_percentage=40 significa 40% academia, 60% colaborador.
    """
    __tablename__ = 'split_configurations'

    id = db.Column(db.Integer, primary_key=True)
    schedule_id = db.Column(db.Integer, db.ForeignKey('class_schedules.id'), nullable=False)

    # Configuracao de split atual
    academy_percentage = db.Column(db.Numeric(5, 2), default=40.00)  # % para academia
    professional_percentage = db.Column(db.Numeric(5, 2), default=60.00)  # % para colaborador

    # Nivel de demanda calculado
    demand_level = db.Column(db.Enum(DemandLevel), default=DemandLevel.STANDARD)
    occupancy_rate = db.Column(db.Numeric(5, 2), default=0.00)  # Taxa de ocupacao media

    # Sugestao do algoritmo (aguardando aprovacao)
    suggested_academy_pct = db.Column(db.Numeric(5, 2))
    suggested_professional_pct = db.Column(db.Numeric(5, 2))
    suggested_demand_level = db.Column(db.Enum(DemandLevel))
    suggestion_pending = db.Column(db.Boolean, default=False)
    suggested_at = db.Column(db.DateTime)

    # Controle
    is_manual_override = db.Column(db.Boolean, default=False)  # Admin ajustou manualmente
    effective_from = db.Column(db.Date, default=date.today)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamentos
    schedule = db.relationship('ClassSchedule', backref=db.backref('split_config', uselist=False))

    def __repr__(self):
        return f'<SplitConfiguration schedule={self.schedule_id} {self.academy_percentage}/{self.professional_percentage}>'

    def apply_suggestion(self):
        """Aplica a sugestao do algoritmo."""
        if self.suggestion_pending and self.suggested_academy_pct:
            self.academy_percentage = self.suggested_academy_pct
            self.professional_percentage = self.suggested_professional_pct
            self.demand_level = self.suggested_demand_level
            self.suggestion_pending = False
            self.is_manual_override = False
            self.updated_at = datetime.utcnow()

    def reject_suggestion(self):
        """Rejeita a sugestao do algoritmo."""
        self.suggestion_pending = False
        self.suggested_academy_pct = None
        self.suggested_professional_pct = None
        self.suggested_demand_level = None

    def set_manual_split(self, academy_pct: Decimal, professional_pct: Decimal):
        """Define split manual (override do algoritmo)."""
        if academy_pct + professional_pct != 100:
            raise ValueError("Soma dos percentuais deve ser 100%")
        self.academy_percentage = academy_pct
        self.professional_percentage = professional_pct
        self.is_manual_override = True
        self.suggestion_pending = False
        self.updated_at = datetime.utcnow()


# =============================================================================
# Entrada de Comissao (por Booking)
# =============================================================================

class CommissionEntry(db.Model):
    """
    Registro de comissao gerada por um booking.

    Cada booking que e finalizado (COMPLETED ou NO_SHOW) gera uma entrada
    de comissao que sera paga ao colaborador.
    """
    __tablename__ = 'commission_entries'

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Valores
    credit_value = db.Column(db.Numeric(10, 2), nullable=False)  # Valor do credito em R$
    academy_percentage = db.Column(db.Numeric(5, 2), nullable=False)  # % aplicado
    professional_percentage = db.Column(db.Numeric(5, 2), nullable=False)

    amount_academy = db.Column(db.Numeric(10, 2), nullable=False)  # Valor para academia
    amount_professional = db.Column(db.Numeric(10, 2), nullable=False)  # Valor para colaborador

    # Contexto
    booking_status = db.Column(db.String(20))  # COMPLETED ou NO_SHOW
    professional_type = db.Column(db.Enum(ProfessionalType))
    demand_level = db.Column(db.Enum(DemandLevel))

    # Status e pagamento
    status = db.Column(db.Enum(CommissionStatus), default=CommissionStatus.PENDING)
    payout_batch_id = db.Column(db.Integer, db.ForeignKey('payout_batches.id'))

    # Auditoria
    processed_at = db.Column(db.DateTime, default=datetime.utcnow)
    paid_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamentos
    booking = db.relationship('Booking', backref=db.backref('commission', uselist=False))
    professional = db.relationship('User', backref='commissions_earned')
    payout_batch = db.relationship('PayoutBatch', backref='entries')

    def __repr__(self):
        return f'<CommissionEntry booking={self.booking_id} professional={self.professional_id} R${self.amount_professional}>'

    @classmethod
    def create_from_booking(cls, booking, credit_value_reais: Decimal, split_config: SplitConfiguration = None):
        """
        Cria entrada de comissao a partir de um booking finalizado.

        Args:
            booking: Booking finalizado (COMPLETED ou NO_SHOW)
            credit_value_reais: Valor do credito em reais
            split_config: Configuracao de split (opcional, usa padrao se None)
        """
        from app.models.booking import BookingStatus

        # Verificar se booking esta finalizado
        if booking.status not in (BookingStatus.COMPLETED, BookingStatus.NO_SHOW):
            raise ValueError(f"Booking deve estar COMPLETED ou NO_SHOW, atual: {booking.status}")

        # Obter instrutor do schedule
        schedule = booking.schedule
        if not schedule or not schedule.instructor_id:
            raise ValueError("Booking sem instrutor associado")

        professional = schedule.instructor
        professional_type = ProfessionalType(professional.professional_type or 'instructor')

        # Regra de No-Show: Nutricionista NAO recebe
        if booking.status == BookingStatus.NO_SHOW and professional_type == ProfessionalType.NUTRITIONIST:
            return None  # Nao gera comissao

        # Obter split config
        if not split_config:
            split_config = schedule.split_config

        # Usar valores padrao se nao tem config
        if split_config:
            academy_pct = split_config.academy_percentage
            prof_pct = split_config.professional_percentage
            demand = split_config.demand_level
        else:
            academy_pct = Decimal('40.00')
            prof_pct = Decimal('60.00')
            demand = DemandLevel.STANDARD

        # Calcular valores
        amount_academy = (credit_value_reais * academy_pct / 100).quantize(Decimal('0.01'))
        amount_professional = (credit_value_reais * prof_pct / 100).quantize(Decimal('0.01'))

        entry = cls(
            booking_id=booking.id,
            professional_id=professional.id,
            credit_value=credit_value_reais,
            academy_percentage=academy_pct,
            professional_percentage=prof_pct,
            amount_academy=amount_academy,
            amount_professional=amount_professional,
            booking_status=booking.status.value,
            professional_type=professional_type,
            demand_level=demand,
            status=CommissionStatus.PENDING
        )

        return entry


# =============================================================================
# Lote de Pagamento (Payout)
# =============================================================================

class PayoutBatch(db.Model):
    """
    Lote de pagamento para um colaborador.

    Agrupa varias entradas de comissao para pagamento em lote.
    """
    __tablename__ = 'payout_batches'

    id = db.Column(db.Integer, primary_key=True)
    professional_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Periodo de referencia
    reference_month = db.Column(db.Integer, nullable=False)  # 1-12
    reference_year = db.Column(db.Integer, nullable=False)

    # Valores totalizados
    total_gross = db.Column(db.Numeric(10, 2), default=0.00)  # Total bruto dos creditos
    total_academy = db.Column(db.Numeric(10, 2), default=0.00)  # Total para academia
    total_professional = db.Column(db.Numeric(10, 2), default=0.00)  # Total para colaborador
    entries_count = db.Column(db.Integer, default=0)  # Quantidade de entradas

    # Status e processamento
    status = db.Column(db.Enum(PayoutStatus), default=PayoutStatus.DRAFT)
    approved_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    approved_at = db.Column(db.DateTime)

    # Pagamento
    paid_at = db.Column(db.DateTime)
    payment_reference = db.Column(db.String(100))  # Referencia bancaria/PIX
    payment_proof_url = db.Column(db.String(500))  # Comprovante

    # Auditoria
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamentos
    professional = db.relationship('User', foreign_keys=[professional_id], backref='payout_batches')
    approved_by = db.relationship('User', foreign_keys=[approved_by_id])

    def __repr__(self):
        return f'<PayoutBatch {self.reference_month}/{self.reference_year} professional={self.professional_id} R${self.total_professional}>'

    def recalculate_totals(self):
        """Recalcula totais baseado nas entries."""
        self.total_gross = sum(e.credit_value for e in self.entries) or Decimal('0.00')
        self.total_academy = sum(e.amount_academy for e in self.entries) or Decimal('0.00')
        self.total_professional = sum(e.amount_professional for e in self.entries) or Decimal('0.00')
        self.entries_count = len(self.entries)

    def approve(self, admin_user):
        """Aprova o lote para pagamento."""
        if self.status != PayoutStatus.PENDING:
            raise ValueError(f"Lote deve estar PENDING para aprovar, atual: {self.status}")

        self.status = PayoutStatus.APPROVED
        self.approved_by_id = admin_user.id
        self.approved_at = datetime.utcnow()

        # Atualizar status das entries
        for entry in self.entries:
            entry.status = CommissionStatus.APPROVED

    def mark_as_paid(self, payment_reference: str = None, proof_url: str = None):
        """Marca o lote como pago."""
        if self.status not in (PayoutStatus.APPROVED, PayoutStatus.PROCESSING):
            raise ValueError(f"Lote deve estar APPROVED ou PROCESSING, atual: {self.status}")

        self.status = PayoutStatus.PAID
        self.paid_at = datetime.utcnow()
        self.payment_reference = payment_reference
        self.payment_proof_url = proof_url

        # Atualizar status das entries
        for entry in self.entries:
            entry.status = CommissionStatus.PAID
            entry.paid_at = datetime.utcnow()


# =============================================================================
# Configuracao Global de Split
# =============================================================================

class SplitSettings(db.Model):
    """Configuracoes globais do sistema de split."""
    __tablename__ = 'split_settings'

    id = db.Column(db.Integer, primary_key=True)

    # Valor do credito em reais (para calculo de comissao)
    credit_value_reais = db.Column(db.Numeric(10, 2), default=15.00)

    # Splits padrao por nivel de demanda
    low_demand_academy_pct = db.Column(db.Numeric(5, 2), default=20.00)
    low_demand_professional_pct = db.Column(db.Numeric(5, 2), default=80.00)

    standard_demand_academy_pct = db.Column(db.Numeric(5, 2), default=40.00)
    standard_demand_professional_pct = db.Column(db.Numeric(5, 2), default=60.00)

    high_demand_academy_pct = db.Column(db.Numeric(5, 2), default=60.00)
    high_demand_professional_pct = db.Column(db.Numeric(5, 2), default=40.00)

    # Thresholds de ocupacao para classificacao
    low_demand_threshold = db.Column(db.Numeric(5, 2), default=40.00)  # < 40% = baixa
    high_demand_threshold = db.Column(db.Numeric(5, 2), default=80.00)  # > 80% = alta

    # Configuracao do job de sugestao
    suggestion_job_enabled = db.Column(db.Boolean, default=True)
    suggestion_lookback_days = db.Column(db.Integer, default=30)  # Dias para analisar

    # Auditoria
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    @classmethod
    def get_settings(cls):
        """Retorna configuracoes (cria se nao existir)."""
        settings = cls.query.first()
        if not settings:
            settings = cls()
            db.session.add(settings)
            db.session.commit()
        return settings

    def get_split_for_demand(self, demand_level: DemandLevel) -> tuple:
        """Retorna (academy_pct, professional_pct) para um nivel de demanda."""
        if demand_level == DemandLevel.LOW:
            return (self.low_demand_academy_pct, self.low_demand_professional_pct)
        elif demand_level == DemandLevel.HIGH:
            return (self.high_demand_academy_pct, self.high_demand_professional_pct)
        else:
            return (self.standard_demand_academy_pct, self.standard_demand_professional_pct)

    def classify_demand(self, occupancy_rate: Decimal) -> DemandLevel:
        """Classifica nivel de demanda baseado na taxa de ocupacao."""
        if occupancy_rate < self.low_demand_threshold:
            return DemandLevel.LOW
        elif occupancy_rate > self.high_demand_threshold:
            return DemandLevel.HIGH
        else:
            return DemandLevel.STANDARD
