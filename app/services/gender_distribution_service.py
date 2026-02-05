# app/services/gender_distribution_service.py

from app import db
from app.models import User, ClassSchedule, Booking, BookingStatus
from app.models.user import Gender
from app.models.modality import Modality
from app.models.schedule_slot_gender import ScheduleSlotGender
from datetime import datetime, date, timedelta
from sqlalchemy import func


class GenderDistributionService:
    """
    Serviço para distribuição automática de gênero em modalidades
    que requerem segregação (ex: FES/Eletroestimulação).

    Algoritmo:
    1. Calcula proporção de clientes masculinos vs femininos
    2. Analisa frequência histórica por horário
    3. Distribui slots de forma homogênea pelo dia
    """

    @staticmethod
    def get_gender_ratio():
        """
        Retorna a proporção de clientes por gênero.

        Returns:
            dict: {'male': float, 'female': float, 'total': int}
        """
        total = User.query.filter(
            User.role == 'student',
            User.is_active == True,
            User.gender.isnot(None)
        ).count()

        if total == 0:
            return {
                'male': 0.5, 
                'female': 0.5, 
                'total': 0,
                'male_count': 0,
                'female_count': 0
            }

        male_count = User.query.filter(
            User.role == 'student',
            User.is_active == True,
            User.gender == Gender.MALE
        ).count()

        female_count = User.query.filter(
            User.role == 'student',
            User.is_active == True,
            User.gender == Gender.FEMALE
        ).count()

        return {
            'male': male_count / total if total > 0 else 0.5,
            'female': female_count / total if total > 0 else 0.5,
            'male_count': male_count,
            'female_count': female_count,
            'total': total
        }

    @staticmethod
    def get_slot_frequency_by_gender(schedule_id, lookback_days=90):
        """
        Analisa frequência histórica de agendamentos por gênero em um horário.

        Args:
            schedule_id: ID do horário
            lookback_days: Dias para análise histórica

        Returns:
            dict: {'male': int, 'female': int, 'dominant': Gender or None}
        """
        cutoff_date = date.today() - timedelta(days=lookback_days)

        # Busca bookings completados neste horário
        bookings = db.session.query(
            User.gender,
            func.count(Booking.id).label('count')
        ).join(
            Booking, Booking.user_id == User.id
        ).filter(
            Booking.schedule_id == schedule_id,
            Booking.date >= cutoff_date,
            Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.COMPLETED]),
            User.gender.isnot(None)
        ).group_by(User.gender).all()

        result = {'male': 0, 'female': 0, 'dominant': None}

        for gender, count in bookings:
            if gender == Gender.MALE:
                result['male'] = count
            elif gender == Gender.FEMALE:
                result['female'] = count

        # Determina gênero dominante
        if result['male'] > result['female']:
            result['dominant'] = Gender.MALE
        elif result['female'] > result['male']:
            result['dominant'] = Gender.FEMALE

        return result

    @staticmethod
    def calculate_slot_distribution(modality_id, target_date):
        """
        Calcula a distribuição de gênero para todos os slots de uma modalidade
        em uma data específica.

        Args:
            modality_id: ID da modalidade
            target_date: Data alvo

        Returns:
            list: [{schedule_id, gender, reason}]
        """
        modality = Modality.query.get(modality_id)
        if not modality or not modality.requires_gender_segregation:
            return []

        # Obter dia da semana
        weekday = target_date.weekday()
        sys_weekday = (weekday + 1) % 7  # Converter para formato do sistema

        # Buscar horários da modalidade
        schedules = ClassSchedule.query.filter_by(
            modality_id=modality_id,
            weekday=sys_weekday,
            is_active=True
        ).order_by(ClassSchedule.start_time).all()

        if not schedules:
            return []

        # Obter proporção de gênero
        ratio = GenderDistributionService.get_gender_ratio()

        # Calcular quantidade de slots para cada gênero
        total_slots = len(schedules)
        male_slots = round(total_slots * ratio['male'])
        female_slots = total_slots - male_slots

        # Se não há clientes suficientes de um gênero, ajustar
        if ratio['male_count'] == 0:
            male_slots = 0
            female_slots = total_slots
        elif ratio['female_count'] == 0:
            male_slots = total_slots
            female_slots = 0

        # Analisar frequência histórica de cada slot
        slot_analysis = []
        for sched in schedules:
            freq = GenderDistributionService.get_slot_frequency_by_gender(sched.id)
            slot_analysis.append({
                'schedule': sched,
                'schedule_id': sched.id,
                'male_freq': freq['male'],
                'female_freq': freq['female'],
                'dominant': freq['dominant'],
                'total_freq': freq['male'] + freq['female']
            })

        # Ordenar por frequência dominante (priorizar slots com mais histórico)
        # Slots com mais frequência feminina vão para o início
        slot_analysis.sort(key=lambda x: (x['female_freq'] - x['male_freq']), reverse=True)

        # Distribuir slots
        distribution = []
        assigned_female = 0
        assigned_male = 0

        for slot in slot_analysis:
            # Verificar se já existe um slot forçado
            existing = ScheduleSlotGender.query.filter_by(
                schedule_id=slot['schedule_id'],
                date=target_date,
                is_forced=True
            ).first()

            if existing:
                # Respeitar slot forçado
                distribution.append({
                    'schedule_id': slot['schedule_id'],
                    'schedule': slot['schedule'],
                    'gender': existing.gender,
                    'reason': 'Definido manualmente'
                })
                if existing.gender == Gender.FEMALE:
                    assigned_female += 1
                else:
                    assigned_male += 1
                continue

            # Atribuir baseado na frequência e proporção
            if slot['dominant'] == Gender.FEMALE and assigned_female < female_slots:
                gender = Gender.FEMALE
                reason = f'Frequência histórica ({slot["female_freq"]} agendamentos femininos)'
                assigned_female += 1
            elif slot['dominant'] == Gender.MALE and assigned_male < male_slots:
                gender = Gender.MALE
                reason = f'Frequência histórica ({slot["male_freq"]} agendamentos masculinos)'
                assigned_male += 1
            elif assigned_female < female_slots:
                gender = Gender.FEMALE
                reason = 'Distribuição proporcional'
                assigned_female += 1
            else:
                gender = Gender.MALE
                reason = 'Distribuição proporcional'
                assigned_male += 1

            distribution.append({
                'schedule_id': slot['schedule_id'],
                'schedule': slot['schedule'],
                'gender': gender,
                'reason': reason
            })

        return distribution

    @staticmethod
    def apply_distribution(modality_id, target_date, force=False):
        """
        Aplica a distribuição de gênero calculada para uma data.

        Args:
            modality_id: ID da modalidade
            target_date: Data alvo
            force: Se True, sobrescreve slots já definidos (não forçados)

        Returns:
            int: Quantidade de slots atualizados
        """
        distribution = GenderDistributionService.calculate_slot_distribution(
            modality_id, target_date
        )

        updated = 0
        for item in distribution:
            # Verificar se já existe
            existing = ScheduleSlotGender.query.filter_by(
                schedule_id=item['schedule_id'],
                date=target_date
            ).first()

            if existing:
                if existing.is_forced:
                    # Não sobrescrever forçados
                    continue
                if not force and existing.gender:
                    # Não sobrescrever se não forçar
                    continue

                existing.gender = item['gender']
                existing.updated_at = datetime.utcnow()
            else:
                slot = ScheduleSlotGender(
                    schedule_id=item['schedule_id'],
                    date=target_date,
                    gender=item['gender'],
                    is_forced=False
                )
                db.session.add(slot)

            updated += 1

        db.session.commit()
        return updated

    @staticmethod
    def get_available_slots_for_user(user, modality_id, target_date):
        """
        Retorna os slots disponíveis para um usuário baseado no seu gênero.

        Args:
            user: Objeto User
            modality_id: ID da modalidade
            target_date: Data alvo

        Returns:
            list: Lista de ClassSchedule disponíveis
        """
        modality = Modality.query.get(modality_id)
        if not modality:
            return []

        # Obter dia da semana
        weekday = target_date.weekday()
        sys_weekday = (weekday + 1) % 7

        # Buscar horários da modalidade
        schedules = ClassSchedule.query.filter_by(
            modality_id=modality_id,
            weekday=sys_weekday,
            is_active=True
        ).order_by(ClassSchedule.start_time).all()

        # Se não requer segregação, retorna todos
        if not modality.requires_gender_segregation:
            return schedules

        # Se usuário não tem gênero definido, não pode agendar em modalidade segregada
        if not user.gender:
            return []

        # Garantir que a distribuição está aplicada
        GenderDistributionService.apply_distribution(modality_id, target_date)

        # Filtrar por gênero do usuário
        available = []
        for sched in schedules:
            slot_gender = ScheduleSlotGender.get_slot_gender(sched.id, target_date)

            # Se não tem gênero definido, assume que pode ser qualquer um
            if slot_gender is None:
                available.append(sched)
            elif slot_gender == user.gender:
                available.append(sched)

        return available

    @staticmethod
    def can_user_book_slot(user, schedule_id, target_date):
        """
        Verifica se um usuário pode agendar um slot específico.

        Returns:
            tuple: (bool, str) - (pode_agendar, motivo)
        """
        schedule = ClassSchedule.query.get(schedule_id)
        if not schedule:
            return False, 'Horário não encontrado'

        modality = schedule.modality
        if not modality.requires_gender_segregation:
            return True, 'OK'

        # Verificar se usuário tem gênero definido
        if not user.gender:
            return False, 'Você precisa definir seu sexo no perfil para agendar esta modalidade'

        # Verificar gênero do slot
        slot_gender = ScheduleSlotGender.get_slot_gender(schedule_id, target_date)

        # Se slot ainda não tem gênero, verificar se há vagas e definir
        if slot_gender is None:
            # Verificar se já existe alguém agendado
            existing_booking = Booking.query.join(User).filter(
                Booking.schedule_id == schedule_id,
                Booking.date == target_date,
                Booking.status == BookingStatus.CONFIRMED,
                User.gender.isnot(None)
            ).first()

            if existing_booking:
                # Definir gênero baseado no primeiro agendamento
                slot_gender = existing_booking.user.gender
                ScheduleSlotGender.get_or_create(
                    schedule_id=schedule_id,
                    slot_date=target_date,
                    gender=slot_gender
                )
            else:
                # Slot vazio, aplica distribuição
                GenderDistributionService.apply_distribution(
                    schedule.modality_id, target_date
                )
                slot_gender = ScheduleSlotGender.get_slot_gender(schedule_id, target_date)

        # Se ainda não tem gênero, permitir (primeiro a agendar define)
        if slot_gender is None:
            return True, 'OK'

        # Verificar compatibilidade
        if slot_gender != user.gender:
            gender_label = 'masculino' if slot_gender == Gender.MALE else 'feminino'
            return False, f'Este horário é exclusivo para público {gender_label}'

        return True, 'OK'


# Singleton
gender_distribution_service = GenderDistributionService()
