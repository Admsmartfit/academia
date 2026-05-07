# app/services/crm_service.py

from datetime import datetime, timedelta
from app import db
from app.models import Booking, BookingStatus, ConversionRule, User
from app.models.xp_ledger import XPLedger
from sqlalchemy import func

class CRMService:
    @staticmethod
    def get_current_streak(user_id):
        """Calcula o streak de dias consecutivos de aulas completadas."""
        total_classes = Booking.query.filter_by(
            user_id=user_id,
            status=BookingStatus.COMPLETED
        ).count()

        if total_classes == 0:
            return 0

        recent_bookings = Booking.query.filter(
            Booking.user_id == user_id,
            Booking.status == BookingStatus.COMPLETED
        ).order_by(Booking.date.desc()).limit(60).all()

        if not recent_bookings:
            return 0

        dates = sorted(set(b.date for b in recent_bookings), reverse=True)
        streak = 0
        current_date = datetime.now().date()
        
        for d in dates:
            diff = (current_date - d).days
            if diff <= 1:
                streak += 1
                current_date = d
            else:
                break
        return streak

    @staticmethod
    def get_user_rank(user):
        """Retorna o ranking do usuario baseado no XP."""
        return db.session.query(
            func.count(User.id)
        ).filter(
            User.role == 'student',
            User.xp > user.xp
        ).scalar() + 1

    @staticmethod
    def get_next_reward_info(user_id):
        """Retorna informacoes sobre a proxima recompensa de gamificacao."""
        xp_available = XPLedger.get_user_available_xp(user_id)
        
        next_reward_rule = ConversionRule.query.filter(
            ConversionRule.is_active == True,
            ConversionRule.xp_required > xp_available
        ).order_by(ConversionRule.xp_required.asc()).first()

        reward_status = None
        xp_to_reward = 0
        
        if next_reward_rule:
            xp_to_reward = next_reward_rule.xp_required - xp_available
            reward_status = 'locked'
        else:
            available_reward = ConversionRule.query.filter(
                ConversionRule.is_active == True,
                ConversionRule.xp_required <= xp_available
            ).order_by(ConversionRule.xp_required.desc()).first()
            
            if available_reward:
                next_reward_rule = available_reward
                reward_status = 'available'
                xp_to_reward = 0

        return {
            'next_reward_rule': next_reward_rule,
            'xp_to_reward': xp_to_reward,
            'reward_status': reward_status,
            'xp_available': xp_available
        }
