# app/services/achievement_checker.py

from app.models import Achievement, UserAchievement, User, Booking, BookingStatus, CriteriaType, ClassSchedule
from app import db
from datetime import datetime, timedelta
from sqlalchemy import func


class AchievementChecker:
    """
    Verifica e desbloqueia conquistas automaticamente
    """

    @staticmethod
    def check_user_achievements(user_id):
        """
        Verifica todas as conquistas possiveis para um usuario
        """
        user = User.query.get(user_id)
        if not user:
            return []

        # Buscar conquistas ativas
        achievements = Achievement.query.filter_by(is_active=True).all()

        # Conquistas ja desbloqueadas
        unlocked_ids = [ua.achievement_id for ua in user.unlocked_achievements]

        newly_unlocked = []

        for achievement in achievements:
            # Pular se ja desbloqueou
            if achievement.id in unlocked_ids:
                continue

            # Verificar criterio
            if AchievementChecker._check_criteria(user, achievement):
                # Desbloquear!
                user_achievement = UserAchievement(
                    user_id=user.id,
                    achievement_id=achievement.id,
                    unlocked_at=datetime.utcnow(),
                    notified=False
                )

                db.session.add(user_achievement)

                # Adicionar XP
                user.xp += achievement.xp_reward

                newly_unlocked.append(achievement)

        db.session.commit()

        # Enviar notificacoes WhatsApp
        AchievementChecker._notify_achievements(user, newly_unlocked)

        return newly_unlocked

    @staticmethod
    def _notify_achievements(user, achievements):
        """
        Envia notificacoes WhatsApp para conquistas desbloqueadas
        """
        if not achievements:
            return

        try:
            from app.services.megaapi import megaapi

            for achievement in achievements:
                try:
                    megaapi.send_template_message(
                        phone=user.phone,
                        template_name='conquista_desbloqueada',
                        variables=[
                            user.name.split()[0],
                            achievement.icon_url or '',
                            achievement.name,
                            str(achievement.xp_reward),
                            'Academia Fitness'
                        ],
                        user_id=user.id
                    )

                    # Marcar como notificado
                    ua = UserAchievement.query.filter_by(
                        user_id=user.id,
                        achievement_id=achievement.id
                    ).first()
                    if ua:
                        ua.notified = True

                except Exception as e:
                    print(f"Erro ao notificar conquista: {e}")

            db.session.commit()

        except ImportError:
            # MegaAPI nao configurado
            pass

    @staticmethod
    def _check_criteria(user, achievement):
        """
        Verifica se usuario atende criterio da conquista
        """
        criteria_type = achievement.criteria_type
        criteria_value = achievement.criteria_value
        criteria_extra = achievement.criteria_extra or {}

        # BOOKINGS_COUNT - X aulas completadas
        if criteria_type == CriteriaType.BOOKINGS_COUNT:
            count = Booking.query.filter_by(
                user_id=user.id,
                status=BookingStatus.COMPLETED
            ).count()
            return count >= criteria_value

        # STREAK_DAYS - X dias consecutivos
        elif criteria_type == CriteriaType.STREAK_DAYS:
            current_streak = AchievementChecker._calculate_streak(user)
            return current_streak >= criteria_value

        # XP_THRESHOLD - Atingir X XP
        elif criteria_type == CriteriaType.XP_THRESHOLD:
            return user.xp >= criteria_value

        # SPECIFIC_MODALITY - X aulas de uma modalidade
        elif criteria_type == CriteriaType.SPECIFIC_MODALITY:
            modality_id = criteria_extra.get('modality_id')
            if not modality_id:
                return False

            count = db.session.query(func.count(Booking.id)).join(
                ClassSchedule, Booking.schedule_id == ClassSchedule.id
            ).filter(
                Booking.user_id == user.id,
                Booking.status == BookingStatus.COMPLETED,
                ClassSchedule.modality_id == modality_id
            ).scalar()

            return count >= criteria_value

        # EARLY_MORNING - X aulas antes das 7h
        elif criteria_type == CriteriaType.EARLY_MORNING:
            from datetime import time

            count = db.session.query(func.count(Booking.id)).join(
                ClassSchedule, Booking.schedule_id == ClassSchedule.id
            ).filter(
                Booking.user_id == user.id,
                Booking.status == BookingStatus.COMPLETED,
                ClassSchedule.start_time < time(7, 0)
            ).scalar()

            return count >= criteria_value

        # PURCHASE_COUNT - X compras realizadas
        elif criteria_type == CriteriaType.PURCHASE_COUNT:
            from app.models import Subscription
            count = Subscription.query.filter_by(user_id=user.id).count()
            return count >= criteria_value

        # REFERRAL_COUNT - Indicar X amigos
        elif criteria_type == CriteriaType.REFERRAL_COUNT:
            # TODO: Implementar sistema de indicacao
            return False

        # CUSTOM - Logica personalizada
        elif criteria_type == CriteriaType.CUSTOM:
            # Custom logic pode ser implementado via criteria_extra
            return False

        return False

    @staticmethod
    def _calculate_streak(user):
        """
        Calcula streak de dias consecutivos com aula
        """
        # Buscar datas unicas com aula completada
        dates = db.session.query(Booking.date).filter_by(
            user_id=user.id,
            status=BookingStatus.COMPLETED
        ).distinct().order_by(Booking.date.desc()).all()

        if not dates:
            return 0

        dates = [d[0] for d in dates]

        # Verificar sequencia de dias consecutivos
        streak = 0
        today = datetime.now().date()

        # Comecar de hoje ou ontem
        if dates[0] == today:
            streak = 1
            expected_date = today - timedelta(days=1)
        elif dates[0] == today - timedelta(days=1):
            streak = 1
            expected_date = today - timedelta(days=2)
        else:
            return 0

        for date in dates[1:]:
            if date == expected_date:
                streak += 1
                expected_date -= timedelta(days=1)
            elif date < expected_date:
                break

        return streak

    @staticmethod
    def check_all_users():
        """
        Verifica conquistas para todos os usuarios (rodar periodicamente)
        """
        users = User.query.filter_by(role='student', is_active=True).all()

        total_unlocked = 0
        for user in users:
            try:
                newly_unlocked = AchievementChecker.check_user_achievements(user.id)
                total_unlocked += len(newly_unlocked)
            except Exception as e:
                print(f"Erro ao verificar conquistas do usuario {user.id}: {e}")

        return total_unlocked


# Singleton
achievement_checker = AchievementChecker()
