# app/services/notification_service.py

from app import db
from app.models import User
from app.models.whatsapp_template import WhatsAppTemplate, TemplateTrigger
from app.services.megaapi import megaapi
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Servico para envio de notificacoes relacionadas a XP e Creditos.
    Integra com WhatsApp via Megaapi.
    """

    @staticmethod
    def notify_xp_conversion(user_id, conversion, is_automatic=True):
        """
        Notifica usuario sobre conversao de XP realizada.

        Args:
            user_id: ID do usuario
            conversion: Objeto XPConversion
            is_automatic: Se foi conversao automatica
        """
        user = User.query.get(user_id)
        if not user or not user.phone:
            logger.warning(f"Usuario {user_id} sem telefone para notificacao")
            return False

        trigger = TemplateTrigger.XP_CONVERSION_AUTO if is_automatic else TemplateTrigger.XP_CONVERSION_MANUAL

        template = WhatsAppTemplate.query.filter_by(
            trigger=trigger,
            is_active=True
        ).first()

        if not template:
            logger.info(f"Template para {trigger.value} nao configurado")
            return False

        try:
            # Variaveis para o template
            variables = [
                user.name.split()[0],  # Primeiro nome
                str(conversion.xp_spent),  # XP gasto
                str(conversion.credits_granted),  # Creditos ganhos
                conversion.wallet.expires_at.strftime('%d/%m/%Y') if conversion.wallet else 'N/A'  # Validade
            ]

            megaapi.send_template_message(
                phone=user.phone,
                template_name=template.template_code,
                variables=variables,
                user_id=user_id
            )

            logger.info(f"Notificacao de conversao enviada para usuario {user_id}")
            return True

        except Exception as e:
            logger.error(f"Erro ao enviar notificacao de conversao: {e}")
            return False

    @staticmethod
    def notify_credits_expiring(user_id, credits_amount, days_remaining, expires_at):
        """
        Notifica usuario sobre creditos proximos a expirar.

        Args:
            user_id: ID do usuario
            credits_amount: Quantidade de creditos expirando
            days_remaining: Dias ate expiracao
            expires_at: Data de expiracao
        """
        user = User.query.get(user_id)
        if not user or not user.phone:
            return False

        # Escolhe trigger baseado nos dias
        if days_remaining <= 1:
            trigger = TemplateTrigger.CREDITS_EXPIRING_1D
        else:
            trigger = TemplateTrigger.CREDITS_EXPIRING

        template = WhatsAppTemplate.query.filter_by(
            trigger=trigger,
            is_active=True
        ).first()

        if not template:
            logger.info(f"Template para {trigger.value} nao configurado")
            return False

        try:
            variables = [
                user.name.split()[0],  # Primeiro nome
                str(credits_amount),  # Quantidade de creditos
                str(days_remaining),  # Dias restantes
                expires_at.strftime('%d/%m/%Y')  # Data de expiracao
            ]

            megaapi.send_template_message(
                phone=user.phone,
                template_name=template.template_code,
                variables=variables,
                user_id=user_id
            )

            logger.info(f"Alerta de creditos expirando enviado para usuario {user_id}")
            return True

        except Exception as e:
            logger.error(f"Erro ao enviar alerta de creditos: {e}")
            return False

    @staticmethod
    def notify_credits_expired(user_id, credits_amount):
        """
        Notifica usuario sobre creditos que expiraram.

        Args:
            user_id: ID do usuario
            credits_amount: Quantidade de creditos que expiraram
        """
        user = User.query.get(user_id)
        if not user or not user.phone:
            return False

        template = WhatsAppTemplate.query.filter_by(
            trigger=TemplateTrigger.CREDITS_EXPIRED,
            is_active=True
        ).first()

        if not template:
            return False

        try:
            variables = [
                user.name.split()[0],  # Primeiro nome
                str(credits_amount)  # Creditos expirados
            ]

            megaapi.send_template_message(
                phone=user.phone,
                template_name=template.template_code,
                variables=variables,
                user_id=user_id
            )

            return True

        except Exception as e:
            logger.error(f"Erro ao enviar notificacao de creditos expirados: {e}")
            return False

    @staticmethod
    def notify_xp_goal_near(user_id, xp_available, rule):
        """
        Notifica usuario quando esta proximo de atingir meta de conversao.

        Args:
            user_id: ID do usuario
            xp_available: XP disponivel atual
            rule: Regra de conversao proxima
        """
        user = User.query.get(user_id)
        if not user or not user.phone:
            return False

        template = WhatsAppTemplate.query.filter_by(
            trigger=TemplateTrigger.XP_GOAL_NEAR,
            is_active=True
        ).first()

        if not template:
            return False

        xp_needed = rule.xp_required - xp_available

        try:
            variables = [
                user.name.split()[0],  # Primeiro nome
                str(xp_needed),  # XP faltando
                str(rule.credits_granted),  # Creditos que ganhara
                rule.name  # Nome da regra
            ]

            megaapi.send_template_message(
                phone=user.phone,
                template_name=template.template_code,
                variables=variables,
                user_id=user_id
            )

            return True

        except Exception as e:
            logger.error(f"Erro ao enviar alerta de meta proxima: {e}")
            return False

    @staticmethod
    def check_and_notify_goal_proximity(user_id, xp_available):
        """
        Verifica se usuario esta proximo de alguma meta e notifica.
        Considera "proximo" quando falta 20% ou menos do XP necessario.

        Args:
            user_id: ID do usuario
            xp_available: XP disponivel atual

        Returns:
            bool: Se alguma notificacao foi enviada
        """
        from app.models.conversion_rule import ConversionRule
        from app.models.xp_conversion import XPConversion

        # Busca regras ativas
        rules = ConversionRule.query.filter_by(is_active=True).all()

        for rule in rules:
            # Verifica se ja pode converter (nao esta "proximo", ja atingiu)
            if xp_available >= rule.xp_required:
                continue

            # Verifica se esta proximo (80-99% do necessario)
            threshold = rule.xp_required * 0.80
            if xp_available >= threshold:
                # Verifica se ja notificou recentemente (evita spam)
                # Usa flag no XP conversion ou cria tabela de notificacoes
                # Por simplicidade, notifica apenas uma vez por dia

                xp_needed = rule.xp_required - xp_available

                NotificationService.notify_xp_goal_near(
                    user_id=user_id,
                    xp_available=xp_available,
                    rule=rule
                )
                return True

        return False


# Singleton
notification_service = NotificationService()
