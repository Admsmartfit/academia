# app/services/dynamic_split_algorithm.py
"""
Algoritmo de Split Dinamico ("Uber Logic").

Analisa a densidade de agendamentos (Occupancy Rate) dos ultimos 30 dias
para cada slot de horario e sugere ajustes de split baseado na demanda:

- Horario de Pico (> 80% ocupacao): Split 60/40 (academia/colaborador)
- Horario Padrao (40-80% ocupacao): Split 40/60
- Horario Ocioso (< 40% ocupacao): Split 20/80

O objetivo e:
- Maximizar lucro em horarios de alta demanda
- Incentivar ocupacao de horarios ociosos com maior comissao para colaboradores
"""

import logging
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import List, Dict, Tuple, Optional

from app import db
from app.models.class_schedule import ClassSchedule
from app.models.booking import Booking, BookingStatus
from app.models.commission import (
    SplitConfiguration, SplitSettings, DemandLevel
)
from app.models.user import User

logger = logging.getLogger(__name__)


class DynamicSplitAlgorithm:
    """
    Motor de sugestao de split dinamico baseado em demanda.

    Inspirado no "Dynamic Pricing" do Uber, ajusta a margem
    conforme oferta/demanda de cada horario.
    """

    def __init__(self):
        self.settings = None
        self.lookback_days = 30

    def get_settings(self) -> SplitSettings:
        """Obtem configuracoes do sistema."""
        if not self.settings:
            self.settings = SplitSettings.get_settings()
        return self.settings

    def calculate_occupancy_rate(
        self,
        schedule: ClassSchedule,
        days: int = None
    ) -> Decimal:
        """
        Calcula taxa de ocupacao media de um horario.

        Args:
            schedule: Horario a analisar
            days: Dias para lookback (padrao: 30)

        Returns:
            Taxa de ocupacao (0-100)
        """
        if days is None:
            days = self.lookback_days

        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        # Contar ocorrencias do horario no periodo
        total_slots = 0
        total_booked = 0

        current = start_date
        while current <= end_date:
            # Verificar se e o dia da semana do schedule
            # weekday() retorna 0=Segunda, mas nosso modelo usa 0=Domingo
            current_weekday = (current.weekday() + 1) % 7

            if current_weekday == schedule.weekday:
                total_slots += schedule.capacity

                # Contar bookings (qualquer status exceto CANCELLED)
                booked = Booking.query.filter(
                    Booking.schedule_id == schedule.id,
                    Booking.date == current,
                    Booking.status != BookingStatus.CANCELLED
                ).count()
                total_booked += booked

            current += timedelta(days=1)

        if total_slots == 0:
            return Decimal('0.00')

        rate = (Decimal(total_booked) / Decimal(total_slots) * 100)
        return rate.quantize(Decimal('0.01'))

    def classify_demand(self, occupancy_rate: Decimal) -> DemandLevel:
        """
        Classifica nivel de demanda baseado na taxa de ocupacao.

        Args:
            occupancy_rate: Taxa de ocupacao (0-100)

        Returns:
            DemandLevel (LOW, STANDARD, HIGH)
        """
        settings = self.get_settings()

        if occupancy_rate < settings.low_demand_threshold:
            return DemandLevel.LOW
        elif occupancy_rate > settings.high_demand_threshold:
            return DemandLevel.HIGH
        else:
            return DemandLevel.STANDARD

    def get_suggested_split(
        self,
        demand_level: DemandLevel
    ) -> Tuple[Decimal, Decimal]:
        """
        Retorna split sugerido para um nivel de demanda.

        Args:
            demand_level: Nivel de demanda

        Returns:
            Tuple (academy_percentage, professional_percentage)
        """
        settings = self.get_settings()
        return settings.get_split_for_demand(demand_level)

    def analyze_schedule(self, schedule: ClassSchedule) -> Dict:
        """
        Analisa um horario e gera sugestao de split.

        Args:
            schedule: Horario a analisar

        Returns:
            Dict com analise e sugestao
        """
        # Calcular ocupacao
        occupancy = self.calculate_occupancy_rate(schedule)

        # Classificar demanda
        demand = self.classify_demand(occupancy)

        # Obter split sugerido
        academy_pct, prof_pct = self.get_suggested_split(demand)

        # Obter split atual
        current_config = schedule.split_config
        if current_config:
            current_academy = current_config.academy_percentage
            current_prof = current_config.professional_percentage
        else:
            current_prof = schedule.current_split_rate or Decimal('60.00')
            current_academy = Decimal('100.00') - current_prof

        # Verificar se precisa ajuste
        needs_adjustment = (
            academy_pct != current_academy or
            prof_pct != current_prof
        )

        return {
            'schedule_id': schedule.id,
            'schedule_info': {
                'weekday': schedule.weekday_name,
                'time': schedule.start_time.strftime('%H:%M'),
                'modality': schedule.modality.name if schedule.modality else 'N/A',
                'instructor': schedule.instructor.name if schedule.instructor else 'N/A',
                'capacity': schedule.capacity
            },
            'analysis': {
                'occupancy_rate': float(occupancy),
                'demand_level': demand.value,
                'lookback_days': self.lookback_days
            },
            'current_split': {
                'academy_pct': float(current_academy),
                'professional_pct': float(current_prof)
            },
            'suggested_split': {
                'academy_pct': float(academy_pct),
                'professional_pct': float(prof_pct)
            },
            'needs_adjustment': needs_adjustment
        }

    def analyze_all_schedules(self) -> List[Dict]:
        """
        Analisa todos os horarios ativos e gera sugestoes.

        Returns:
            Lista de analises
        """
        schedules = ClassSchedule.query.filter_by(is_active=True).all()

        analyses = []
        for schedule in schedules:
            analysis = self.analyze_schedule(schedule)
            analyses.append(analysis)

        # Ordenar por necessidade de ajuste e ocupacao
        analyses.sort(
            key=lambda x: (not x['needs_adjustment'], -x['analysis']['occupancy_rate'])
        )

        return analyses

    def generate_suggestions(self) -> Dict:
        """
        Gera sugestoes de ajuste de split para revisao do admin.

        Cria SplitConfiguration com suggestion_pending=True para
        cada horario que precisa de ajuste.

        Returns:
            Estatisticas da geracao
        """
        settings = self.get_settings()

        if not settings.suggestion_job_enabled:
            logger.info("Job de sugestao de split desabilitado")
            return {'status': 'disabled'}

        self.lookback_days = settings.suggestion_lookback_days

        schedules = ClassSchedule.query.filter_by(is_active=True).all()

        stats = {
            'total_schedules': len(schedules),
            'suggestions_created': 0,
            'no_change_needed': 0,
            'errors': 0
        }

        for schedule in schedules:
            try:
                # Analisar horario
                occupancy = self.calculate_occupancy_rate(schedule)
                demand = self.classify_demand(occupancy)
                academy_pct, prof_pct = self.get_suggested_split(demand)

                # Atualizar cache de ocupacao no schedule
                schedule.avg_occupancy_rate = occupancy

                # Obter ou criar SplitConfiguration
                config = schedule.split_config
                if not config:
                    config = SplitConfiguration(
                        schedule_id=schedule.id,
                        academy_percentage=Decimal('40.00'),
                        professional_percentage=Decimal('60.00'),
                        demand_level=DemandLevel.STANDARD
                    )
                    db.session.add(config)

                # Verificar se precisa ajuste (e nao esta em override manual)
                needs_change = (
                    not config.is_manual_override and
                    (config.academy_percentage != academy_pct or
                     config.professional_percentage != prof_pct)
                )

                if needs_change:
                    config.suggested_academy_pct = academy_pct
                    config.suggested_professional_pct = prof_pct
                    config.suggested_demand_level = demand
                    config.suggestion_pending = True
                    config.suggested_at = datetime.utcnow()
                    config.occupancy_rate = occupancy
                    stats['suggestions_created'] += 1
                else:
                    config.occupancy_rate = occupancy
                    config.demand_level = demand
                    stats['no_change_needed'] += 1

            except Exception as e:
                logger.error(f"Erro ao analisar schedule {schedule.id}: {e}")
                stats['errors'] += 1

        db.session.commit()

        logger.info(f"Sugestoes de split geradas: {stats}")
        return stats

    def get_pending_suggestions(self) -> List[Dict]:
        """
        Retorna sugestoes pendentes de aprovacao.

        Returns:
            Lista de sugestoes para revisao do admin
        """
        configs = SplitConfiguration.query.filter_by(
            suggestion_pending=True
        ).all()

        suggestions = []
        for config in configs:
            schedule = config.schedule
            suggestions.append({
                'config_id': config.id,
                'schedule_id': schedule.id,
                'schedule_info': {
                    'weekday': schedule.weekday_name,
                    'time': schedule.start_time.strftime('%H:%M'),
                    'modality': schedule.modality.name if schedule.modality else 'N/A',
                    'instructor': schedule.instructor.name if schedule.instructor else 'N/A'
                },
                'occupancy_rate': float(config.occupancy_rate),
                'current_split': {
                    'academy_pct': float(config.academy_percentage),
                    'professional_pct': float(config.professional_percentage),
                    'demand_level': config.demand_level.value if config.demand_level else 'standard'
                },
                'suggested_split': {
                    'academy_pct': float(config.suggested_academy_pct),
                    'professional_pct': float(config.suggested_professional_pct),
                    'demand_level': config.suggested_demand_level.value if config.suggested_demand_level else 'standard'
                },
                'suggested_at': config.suggested_at.isoformat() if config.suggested_at else None
            })

        return suggestions

    def apply_suggestion(self, config_id: int, admin_user: User) -> bool:
        """
        Aplica uma sugestao de split.

        Args:
            config_id: ID da SplitConfiguration
            admin_user: Usuario admin que aprovou

        Returns:
            True se aplicada com sucesso
        """
        config = SplitConfiguration.query.get(config_id)
        if not config or not config.suggestion_pending:
            return False

        config.apply_suggestion()

        # Atualizar current_split_rate no schedule
        schedule = config.schedule
        schedule.current_split_rate = config.professional_percentage

        db.session.commit()

        logger.info(
            f"Sugestao de split aplicada: Schedule {schedule.id}, "
            f"Split {config.academy_percentage}/{config.professional_percentage}, "
            f"Aprovado por {admin_user.name}"
        )

        return True

    def reject_suggestion(self, config_id: int, admin_user: User) -> bool:
        """
        Rejeita uma sugestao de split.

        Args:
            config_id: ID da SplitConfiguration
            admin_user: Usuario admin que rejeitou

        Returns:
            True se rejeitada com sucesso
        """
        config = SplitConfiguration.query.get(config_id)
        if not config or not config.suggestion_pending:
            return False

        config.reject_suggestion()
        db.session.commit()

        logger.info(
            f"Sugestao de split rejeitada: Schedule {config.schedule_id}, "
            f"Rejeitado por {admin_user.name}"
        )

        return True

    def apply_all_suggestions(self, admin_user: User) -> int:
        """
        Aplica todas as sugestoes pendentes.

        Returns:
            Quantidade de sugestoes aplicadas
        """
        configs = SplitConfiguration.query.filter_by(
            suggestion_pending=True
        ).all()

        count = 0
        for config in configs:
            if self.apply_suggestion(config.id, admin_user):
                count += 1

        return count

    def set_manual_split(
        self,
        schedule_id: int,
        academy_pct: Decimal,
        professional_pct: Decimal,
        admin_user: User
    ) -> SplitConfiguration:
        """
        Define split manual para um horario (override do algoritmo).

        Args:
            schedule_id: ID do schedule
            academy_pct: % para academia
            professional_pct: % para colaborador
            admin_user: Usuario admin

        Returns:
            SplitConfiguration atualizada
        """
        if academy_pct + professional_pct != 100:
            raise ValueError("Soma dos percentuais deve ser 100%")

        schedule = ClassSchedule.query.get(schedule_id)
        if not schedule:
            raise ValueError(f"Schedule {schedule_id} nao encontrado")

        config = schedule.split_config
        if not config:
            config = SplitConfiguration(schedule_id=schedule_id)
            db.session.add(config)

        config.set_manual_split(academy_pct, professional_pct)

        # Atualizar schedule
        schedule.current_split_rate = professional_pct

        db.session.commit()

        logger.info(
            f"Split manual definido: Schedule {schedule_id}, "
            f"Split {academy_pct}/{professional_pct}, "
            f"Por {admin_user.name}"
        )

        return config


# =============================================================================
# Instancia global
# =============================================================================

dynamic_split = DynamicSplitAlgorithm()
