# app/services/split_service.py
"""
Servico de Split Bancario Dinamico.

Responsavel por:
- Calcular e processar comissoes de colaboradores
- Aplicar regras de split dinamico baseado em demanda
- Gerar lotes de pagamento (payouts)
- Processar expiracoes de creditos (lucro academia)
"""

import logging
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import List, Dict, Optional, Tuple

from app import db
from app.models.booking import Booking, BookingStatus
from app.models.class_schedule import ClassSchedule
from app.models.user import User, ProfessionalType
from app.models.commission import (
    CommissionEntry, CommissionStatus,
    SplitConfiguration, SplitSettings,
    PayoutBatch, PayoutStatus,
    DemandLevel, CollaboratorBankInfo
)

logger = logging.getLogger(__name__)


class SplitService:
    """Servico principal de gestao de split e comissoes."""

    def __init__(self):
        self.settings = None

    def get_settings(self) -> SplitSettings:
        """Obtem configuracoes do sistema (com cache)."""
        if not self.settings:
            self.settings = SplitSettings.get_settings()
        return self.settings

    # =========================================================================
    # Processamento de Comissoes
    # =========================================================================

    def process_booking_commission(self, booking: Booking) -> Optional[CommissionEntry]:
        """
        Processa comissao para um booking finalizado.

        Deve ser chamado quando booking muda para COMPLETED ou NO_SHOW.

        Args:
            booking: Booking finalizado

        Returns:
            CommissionEntry criada ou None se nao aplicavel
        """
        # Verificar se ja tem comissao
        if booking.commission:
            logger.warning(f"Booking {booking.id} ja tem comissao processada")
            return booking.commission

        # Verificar status
        if booking.status not in (BookingStatus.COMPLETED, BookingStatus.NO_SHOW):
            logger.warning(f"Booking {booking.id} nao esta finalizado: {booking.status}")
            return None

        # Obter schedule e instrutor
        schedule = booking.schedule
        if not schedule:
            logger.error(f"Booking {booking.id} sem schedule associado")
            return None

        instructor = schedule.instructor
        if not instructor:
            logger.error(f"Schedule {schedule.id} sem instrutor")
            return None

        # Determinar tipo de profissional
        prof_type = instructor.professional_type or ProfessionalType.INSTRUCTOR

        # Regra: Nutricionista NAO recebe em No-Show
        if booking.status == BookingStatus.NO_SHOW and prof_type == ProfessionalType.NUTRITIONIST:
            logger.info(f"Booking {booking.id}: No-Show de nutricionista, sem comissao")
            return None

        # Obter valor do credito
        settings = self.get_settings()
        credit_value = settings.credit_value_reais * booking.cost_at_booking

        # Obter split configuration
        split_config = schedule.split_config
        if split_config:
            academy_pct = split_config.academy_percentage
            prof_pct = split_config.professional_percentage
            demand = split_config.demand_level
        else:
            # Usar split do schedule ou padrao
            prof_pct = schedule.current_split_rate or Decimal('60.00')
            academy_pct = Decimal('100.00') - prof_pct
            demand = DemandLevel.STANDARD

        # Calcular valores
        amount_academy = (credit_value * academy_pct / 100).quantize(Decimal('0.01'))
        amount_professional = (credit_value * prof_pct / 100).quantize(Decimal('0.01'))

        # Criar entrada de comissao
        entry = CommissionEntry(
            booking_id=booking.id,
            professional_id=instructor.id,
            credit_value=credit_value,
            academy_percentage=academy_pct,
            professional_percentage=prof_pct,
            amount_academy=amount_academy,
            amount_professional=amount_professional,
            booking_status=booking.status.value,
            professional_type=prof_type,
            demand_level=demand,
            status=CommissionStatus.PENDING
        )

        db.session.add(entry)
        db.session.commit()

        logger.info(
            f"Comissao criada: Booking {booking.id}, "
            f"Instrutor {instructor.name}, "
            f"R${amount_professional} ({prof_pct}%)"
        )

        return entry

    def process_pending_bookings(self) -> Dict:
        """
        Processa todos os bookings finalizados sem comissao.

        Retorna estatisticas do processamento.
        """
        # Buscar bookings finalizados sem comissao
        bookings = Booking.query.filter(
            Booking.status.in_([BookingStatus.COMPLETED, BookingStatus.NO_SHOW]),
            ~Booking.id.in_(
                db.session.query(CommissionEntry.booking_id)
            )
        ).all()

        stats = {
            'total': len(bookings),
            'processed': 0,
            'skipped': 0,
            'errors': 0
        }

        for booking in bookings:
            try:
                entry = self.process_booking_commission(booking)
                if entry:
                    stats['processed'] += 1
                else:
                    stats['skipped'] += 1
            except Exception as e:
                logger.error(f"Erro ao processar booking {booking.id}: {e}")
                stats['errors'] += 1

        logger.info(f"Processamento de comissoes: {stats}")
        return stats

    # =========================================================================
    # Gestao de Payouts
    # =========================================================================

    def create_payout_batch(
        self,
        professional_id: int,
        month: int,
        year: int
    ) -> PayoutBatch:
        """
        Cria lote de pagamento para um colaborador.

        Args:
            professional_id: ID do colaborador
            month: Mes de referencia (1-12)
            year: Ano de referencia

        Returns:
            PayoutBatch criado
        """
        # Verificar se ja existe
        existing = PayoutBatch.query.filter_by(
            professional_id=professional_id,
            reference_month=month,
            reference_year=year
        ).first()

        if existing:
            return existing

        # Criar novo batch
        batch = PayoutBatch(
            professional_id=professional_id,
            reference_month=month,
            reference_year=year,
            status=PayoutStatus.DRAFT
        )
        db.session.add(batch)
        db.session.flush()

        # Associar comissoes pendentes do periodo
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)

        entries = CommissionEntry.query.filter(
            CommissionEntry.professional_id == professional_id,
            CommissionEntry.status == CommissionStatus.PENDING,
            CommissionEntry.processed_at >= datetime.combine(start_date, datetime.min.time()),
            CommissionEntry.processed_at < datetime.combine(end_date, datetime.min.time())
        ).all()

        for entry in entries:
            entry.payout_batch_id = batch.id

        batch.recalculate_totals()
        batch.status = PayoutStatus.PENDING

        db.session.commit()

        logger.info(
            f"Payout batch criado: {month}/{year}, "
            f"Colaborador {professional_id}, "
            f"{batch.entries_count} entradas, "
            f"R${batch.total_professional}"
        )

        return batch

    def generate_monthly_payouts(self, month: int, year: int) -> List[PayoutBatch]:
        """
        Gera lotes de pagamento para todos os colaboradores do mes.

        Returns:
            Lista de PayoutBatch criados
        """
        # Buscar colaboradores com comissoes no periodo
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)

        professional_ids = db.session.query(
            CommissionEntry.professional_id
        ).filter(
            CommissionEntry.status == CommissionStatus.PENDING,
            CommissionEntry.processed_at >= datetime.combine(start_date, datetime.min.time()),
            CommissionEntry.processed_at < datetime.combine(end_date, datetime.min.time())
        ).distinct().all()

        batches = []
        for (prof_id,) in professional_ids:
            batch = self.create_payout_batch(prof_id, month, year)
            batches.append(batch)

        logger.info(f"Gerados {len(batches)} lotes de pagamento para {month}/{year}")
        return batches

    # =========================================================================
    # Extrato do Colaborador
    # =========================================================================

    def get_collaborator_statement(
        self,
        professional_id: int,
        month: int = None,
        year: int = None
    ) -> Dict:
        """
        Gera extrato de comissoes do colaborador.

        Args:
            professional_id: ID do colaborador
            month: Mes (opcional, padrao: mes atual)
            year: Ano (opcional, padrao: ano atual)

        Returns:
            Dict com dados do extrato
        """
        if not month:
            month = datetime.now().month
        if not year:
            year = datetime.now().year

        professional = User.query.get(professional_id)
        if not professional:
            raise ValueError(f"Colaborador {professional_id} nao encontrado")

        # Periodo
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)

        # Buscar comissoes
        entries = CommissionEntry.query.filter(
            CommissionEntry.professional_id == professional_id,
            CommissionEntry.processed_at >= datetime.combine(start_date, datetime.min.time()),
            CommissionEntry.processed_at < datetime.combine(end_date, datetime.min.time())
        ).order_by(CommissionEntry.processed_at).all()

        # Calcular totais
        total_gross = sum(e.credit_value for e in entries)
        total_academy = sum(e.amount_academy for e in entries)
        total_professional = sum(e.amount_professional for e in entries)

        # Agrupar por status
        by_status = {}
        for entry in entries:
            status = entry.status.value
            if status not in by_status:
                by_status[status] = {'count': 0, 'amount': Decimal('0.00')}
            by_status[status]['count'] += 1
            by_status[status]['amount'] += entry.amount_professional

        # Detalhes das entradas
        details = []
        for entry in entries:
            booking = entry.booking
            schedule = booking.schedule if booking else None
            modality = schedule.modality if schedule else None

            details.append({
                'id': entry.id,
                'date': booking.date if booking else None,
                'time': schedule.start_time if schedule else None,
                'client_name': booking.user.name if booking and booking.user else 'N/A',
                'modality': modality.name if modality else 'N/A',
                'status': entry.booking_status,
                'credit_value': float(entry.credit_value),
                'split_pct': float(entry.professional_percentage),
                'amount': float(entry.amount_professional),
                'commission_status': entry.status.value
            })

        return {
            'professional': {
                'id': professional.id,
                'name': professional.name,
                'email': professional.email,
                'cpf': professional.cpf,
                'type': professional.professional_type.value if professional.professional_type else 'instructor'
            },
            'period': {
                'month': month,
                'year': year,
                'start_date': start_date.isoformat(),
                'end_date': (end_date - timedelta(days=1)).isoformat()
            },
            'summary': {
                'total_entries': len(entries),
                'total_gross': float(total_gross),
                'total_academy': float(total_academy),
                'total_professional': float(total_professional),
                'by_status': {k: {'count': v['count'], 'amount': float(v['amount'])} for k, v in by_status.items()}
            },
            'entries': details
        }

    # =========================================================================
    # Creditos Expirados (Lucro Academia)
    # =========================================================================

    def process_expired_credits_revenue(self) -> Dict:
        """
        Processa creditos expirados como lucro da academia.

        Creditos nao utilizados dentro da validade revertem 100%
        para a academia, sem gerar repasse aos colaboradores.

        Returns:
            Estatisticas do processamento
        """
        from app.models.credit_wallet import CreditWallet

        # Buscar wallets expiradas nao processadas
        expired_wallets = CreditWallet.query.filter(
            CreditWallet.expires_at < datetime.utcnow(),
            CreditWallet.credits_remaining > 0,
            CreditWallet.is_expired == False
        ).all()

        settings = self.get_settings()
        total_credits = 0
        total_value = Decimal('0.00')

        for wallet in expired_wallets:
            credits = wallet.credits_remaining
            value = settings.credit_value_reais * credits

            total_credits += credits
            total_value += value

            wallet.is_expired = True
            wallet.credits_remaining = 0

            logger.info(
                f"Creditos expirados: User {wallet.user_id}, "
                f"{credits} creditos = R${value} (lucro academia)"
            )

        db.session.commit()

        return {
            'wallets_processed': len(expired_wallets),
            'total_credits_expired': total_credits,
            'total_revenue': float(total_value)
        }


# =============================================================================
# Instancia global
# =============================================================================

split_service = SplitService()
