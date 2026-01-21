# app/services/xp_manager.py

from app import db
from app.models import Booking, BookingStatus
from datetime import time


class XPManager:
    """
    Gerencia atribuicao de XP
    """

    XP_VALUES = {
        'checkin': 10,
        'checkin_first_of_day': 15,  # Bonus primeira aula do dia
        'checkin_early_morning': 13,  # Bonus antes das 7h
        'purchase_5': 25,
        'purchase_10': 50,
        'purchase_20': 100,
        'streak_3_days': 30,
        'streak_7_days': 100,
        'referral': 100,
        'profile_complete': 20,
    }

    PENALTIES = {
        'cancel_late': -5,      # Cancelar 2-3h antes
        'cancel_very_late': -10,  # Cancelar < 2h
        'no_show': -50,         # Nao comparecer
    }

    @staticmethod
    def award_checkin_xp(booking):
        """
        Calcula e atribui XP do check-in
        """
        user = booking.user
        base_xp = XPManager.XP_VALUES['checkin']
        bonus_xp = 0

        # Bonus: Primeira aula do dia
        today = booking.date
        other_checkins_today = Booking.query.filter(
            Booking.user_id == user.id,
            Booking.date == today,
            Booking.status == BookingStatus.COMPLETED,
            Booking.id != booking.id
        ).count()

        if other_checkins_today == 0:
            bonus_xp += (XPManager.XP_VALUES['checkin_first_of_day'] - base_xp)

        # Bonus: Aula cedo (antes das 7h)
        if booking.schedule.start_time < time(7, 0):
            bonus_xp += (XPManager.XP_VALUES['checkin_early_morning'] - base_xp)

        total_xp = base_xp + bonus_xp

        # Atribuir
        user.xp += total_xp
        booking.xp_earned = total_xp

        db.session.commit()

        return total_xp

    @staticmethod
    def award_purchase_xp(user, credits_purchased):
        """
        Atribui XP baseado na quantidade de creditos comprados
        """
        xp_to_add = 0

        if credits_purchased >= 20:
            xp_to_add = XPManager.XP_VALUES['purchase_20']
        elif credits_purchased >= 10:
            xp_to_add = XPManager.XP_VALUES['purchase_10']
        elif credits_purchased >= 5:
            xp_to_add = XPManager.XP_VALUES['purchase_5']

        if xp_to_add > 0:
            user.xp += xp_to_add
            db.session.commit()

        return xp_to_add

    @staticmethod
    def apply_penalty(user, penalty_type):
        """
        Aplica penalidade de XP
        """
        if penalty_type not in XPManager.PENALTIES:
            return 0

        penalty = XPManager.PENALTIES[penalty_type]
        user.xp = max(0, user.xp + penalty)  # XP nao pode ficar negativo
        db.session.commit()

        return penalty

    @staticmethod
    def award_streak_xp(user, streak_days):
        """
        Atribui XP por streak de dias consecutivos
        """
        xp_to_add = 0

        if streak_days >= 7:
            xp_to_add = XPManager.XP_VALUES['streak_7_days']
        elif streak_days >= 3:
            xp_to_add = XPManager.XP_VALUES['streak_3_days']

        if xp_to_add > 0:
            user.xp += xp_to_add
            db.session.commit()

        return xp_to_add

    @staticmethod
    def award_referral_xp(user):
        """
        Atribui XP por indicacao
        """
        xp_to_add = XPManager.XP_VALUES['referral']
        user.xp += xp_to_add
        db.session.commit()

        return xp_to_add

    @staticmethod
    def award_profile_complete_xp(user):
        """
        Atribui XP por completar perfil
        """
        xp_to_add = XPManager.XP_VALUES['profile_complete']
        user.xp += xp_to_add
        db.session.commit()

        return xp_to_add


# Singleton
xp_manager = XPManager()
