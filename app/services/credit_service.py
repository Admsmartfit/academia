# app/services/credit_service.py

from app import db
from app.models.credit_wallet import CreditWallet, CreditSourceType
from app.models.xp_ledger import XPLedger, XPSourceType
from app.models.conversion_rule import ConversionRule
from app.models.xp_conversion import XPConversion
from datetime import datetime, timedelta


class CreditService:
    """
    Servico para gerenciamento de creditos e conversao de XP.
    Implementa logica FIFO (primeiro a vencer, primeiro a usar).
    """

    # =========================================
    # CREDIT WALLET OPERATIONS
    # =========================================

    @staticmethod
    def create_wallet(user_id, credits, source_type, source_id=None, validity_days=30):
        """
        Cria uma nova carteira de creditos para o usuario.

        Args:
            user_id: ID do usuario
            credits: Quantidade de creditos
            source_type: Tipo de origem (CreditSourceType)
            source_id: ID da origem (compra, conversao, etc)
            validity_days: Dias de validade

        Returns:
            CreditWallet criada
        """
        expires_at = datetime.utcnow() + timedelta(days=validity_days)

        wallet = CreditWallet(
            user_id=user_id,
            credits_initial=credits,
            credits_remaining=credits,
            source_type=source_type,
            source_id=source_id,
            expires_at=expires_at
        )
        db.session.add(wallet)
        db.session.flush()  # Para obter o ID

        # Atualiza cache do usuario
        from app.models import User
        user = User.query.get(user_id)
        if user:
            user.refresh_credits_cache()

        return wallet

    @staticmethod
    def use_credits(user_id, amount):
        """
        Debita creditos usando logica FIFO (primeiro a vencer, primeiro a usar).

        Args:
            user_id: ID do usuario
            amount: Quantidade de creditos a debitar

        Returns:
            dict com:
                - success: bool
                - debited: int (quantidade debitada)
                - wallets_used: list (detalhes das carteiras usadas)
                - error: str (se houver erro)
        """
        wallets = CreditWallet.get_user_active_wallets(user_id, order_fifo=True)
        total_available = sum(w.credits_remaining for w in wallets)

        if total_available < amount:
            return {
                'success': False,
                'debited': 0,
                'wallets_used': [],
                'error': f'Creditos insuficientes. Disponivel: {total_available}, Necessario: {amount}'
            }

        remaining = amount
        wallets_used = []

        for wallet in wallets:
            if remaining <= 0:
                break

            debited = wallet.use_credits(remaining)
            if debited > 0:
                wallets_used.append({
                    'wallet_id': wallet.id,
                    'debited': debited,
                    'expires_at': wallet.expires_at,
                    'source_type': wallet.source_type.value
                })
                remaining -= debited

        db.session.commit()

        # Atualiza cache do usuario
        from app.models import User
        user = User.query.get(user_id)
        if user:
            user.refresh_credits_cache()
            db.session.commit()

        return {
            'success': True,
            'debited': amount,
            'wallets_used': wallets_used,
            'error': None
        }

    @staticmethod
    def preview_credit_usage(user_id, amount):
        """
        Mostra preview de quais carteiras serao usadas sem debitar.
        Util para mostrar ao usuario antes de confirmar agendamento.

        Args:
            user_id: ID do usuario
            amount: Quantidade de creditos necessarios

        Returns:
            dict com:
                - can_afford: bool
                - total_available: int
                - wallets_preview: list (detalhes das carteiras que serao usadas)
        """
        wallets = CreditWallet.get_user_active_wallets(user_id, order_fifo=True)
        total_available = sum(w.credits_remaining for w in wallets)

        if total_available < amount:
            return {
                'can_afford': False,
                'total_available': total_available,
                'wallets_preview': []
            }

        remaining = amount
        wallets_preview = []

        for wallet in wallets:
            if remaining <= 0:
                break

            to_use = min(remaining, wallet.credits_remaining)
            wallets_preview.append({
                'wallet_id': wallet.id,
                'credits_to_use': to_use,
                'credits_remaining_after': wallet.credits_remaining - to_use,
                'expires_at': wallet.expires_at.strftime('%d/%m/%Y'),
                'days_until_expiry': wallet.days_until_expiry,
                'source_type': wallet.source_description
            })
            remaining -= to_use

        return {
            'can_afford': True,
            'total_available': total_available,
            'wallets_preview': wallets_preview
        }

    @staticmethod
    def refund_credits(user_id, amount, reason="Estorno"):
        """
        Estorna creditos para o usuario (cria nova wallet de refund).

        Args:
            user_id: ID do usuario
            amount: Quantidade de creditos a estornar
            reason: Motivo do estorno

        Returns:
            CreditWallet criada
        """
        # Estornos tem validade de 30 dias
        return CreditService.create_wallet(
            user_id=user_id,
            credits=amount,
            source_type=CreditSourceType.REFUND,
            validity_days=30
        )

    @staticmethod
    def expire_wallets():
        """
        Job para marcar carteiras expiradas.
        Deve ser executado periodicamente (cron).

        Returns:
            int: Quantidade de carteiras expiradas
        """
        now = datetime.utcnow()

        expired_wallets = CreditWallet.query.filter(
            CreditWallet.is_expired == False,
            CreditWallet.expires_at <= now
        ).all()

        count = 0
        user_ids = set()

        for wallet in expired_wallets:
            wallet.is_expired = True
            user_ids.add(wallet.user_id)
            count += 1

        db.session.commit()

        # Atualiza caches dos usuarios afetados
        from app.models import User
        for user_id in user_ids:
            user = User.query.get(user_id)
            if user:
                user.refresh_credits_cache()

        db.session.commit()

        return count

    # =========================================
    # XP CONVERSION OPERATIONS
    # =========================================

    @staticmethod
    def get_available_rules(user_id):
        """
        Retorna regras de conversao disponiveis para o usuario.

        Args:
            user_id: ID do usuario

        Returns:
            list de dicts com regras e status de disponibilidade
        """
        from app.models import User
        user = User.query.get(user_id)
        if not user:
            return []

        # Obtem XP disponivel
        xp_available = XPLedger.get_user_available_xp(user_id)

        # Busca regras ativas ordenadas por prioridade
        rules = ConversionRule.query.filter_by(is_active=True).order_by(
            ConversionRule.priority.desc(),
            ConversionRule.xp_required.asc()
        ).all()

        result = []
        for rule in rules:
            is_available, reason = rule.is_available_for_user(user_id, xp_available)
            result.append({
                'rule_id': rule.id,
                'name': rule.name,
                'description': rule.description,
                'xp_required': rule.xp_required,
                'credits_granted': rule.credits_granted,
                'validity_days': rule.credit_validity_days,
                'is_automatic': rule.is_automatic,
                'is_available': is_available,
                'reason': reason,
                'user_usage_count': rule.get_user_usage_count(user_id),
                'max_uses': rule.max_uses_per_user
            })

        return result

    @staticmethod
    def convert_xp(user_id, rule_id, is_automatic=False):
        """
        Executa conversao de XP em creditos.

        Args:
            user_id: ID do usuario
            rule_id: ID da regra de conversao
            is_automatic: Se foi conversao automatica

        Returns:
            dict com:
                - success: bool
                - conversion: XPConversion (se sucesso)
                - wallet: CreditWallet (se sucesso)
                - error: str (se erro)
        """
        from app.models import User
        user = User.query.get(user_id)
        if not user:
            return {'success': False, 'error': 'Usuario nao encontrado'}

        rule = ConversionRule.query.get(rule_id)
        if not rule:
            return {'success': False, 'error': 'Regra nao encontrada'}

        # Obtem XP disponivel
        xp_available = XPLedger.get_user_available_xp(user_id)

        # Verifica disponibilidade
        is_available, reason = rule.is_available_for_user(user_id, xp_available)
        if not is_available:
            return {'success': False, 'error': reason}

        # Inicia transacao
        try:
            # 1. Consome XP do ledger (FIFO por expiracao)
            success = XPLedger.consume_xp_for_conversion(user_id, rule.xp_required)
            if not success:
                return {'success': False, 'error': 'Falha ao consumir XP'}

            # 2. Cria wallet com os creditos
            wallet = CreditService.create_wallet(
                user_id=user_id,
                credits=rule.credits_granted,
                source_type=CreditSourceType.CONVERSION,
                validity_days=rule.credit_validity_days
            )

            # 3. Registra a conversao
            conversion = XPConversion(
                user_id=user_id,
                rule_id=rule_id,
                xp_spent=rule.xp_required,
                credits_granted=rule.credits_granted,
                wallet_id=wallet.id,
                is_automatic=is_automatic
            )
            db.session.add(conversion)

            # 4. Atualiza caches do usuario
            user.refresh_xp_cache()
            user.refresh_credits_cache()

            db.session.commit()

            return {
                'success': True,
                'conversion': conversion,
                'wallet': wallet,
                'error': None
            }

        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': f'Erro na conversao: {str(e)}'}

    @staticmethod
    def check_automatic_conversions(user_id):
        """
        Verifica e executa conversoes automaticas para o usuario.
        Chamado apos ganho de XP.

        Args:
            user_id: ID do usuario

        Returns:
            list de conversoes realizadas
        """
        # Busca regras automaticas ativas
        rules = ConversionRule.query.filter_by(
            is_active=True,
            is_automatic=True
        ).order_by(ConversionRule.priority.desc()).all()

        xp_available = XPLedger.get_user_available_xp(user_id)
        conversions = []

        for rule in rules:
            # Verifica se pode converter
            is_available, _ = rule.is_available_for_user(user_id, xp_available)

            if is_available:
                result = CreditService.convert_xp(user_id, rule.id, is_automatic=True)
                if result['success']:
                    conversions.append(result['conversion'])
                    # Atualiza XP disponivel para proxima iteracao
                    xp_available = XPLedger.get_user_available_xp(user_id)

        return conversions

    # =========================================
    # USER SUMMARY
    # =========================================

    @staticmethod
    def get_user_summary(user_id):
        """
        Retorna resumo completo de XP e creditos do usuario.

        Args:
            user_id: ID do usuario

        Returns:
            dict com resumo completo
        """
        from app.models import User
        user = User.query.get(user_id)
        if not user:
            return None

        # XP
        xp_total = XPLedger.get_user_total_xp(user_id) or user.xp  # Fallback para XP antigo
        xp_available = XPLedger.get_user_available_xp(user_id)
        xp_converted = XPLedger.get_user_converted_xp(user_id)

        # Creditos
        wallets = CreditWallet.get_user_active_wallets(user_id)
        credits_total = sum(w.credits_remaining for w in wallets)
        expiring_soon = CreditWallet.get_expiring_soon(user_id, days=7)
        credits_expiring = sum(w.credits_remaining for w in expiring_soon)

        # Conversoes
        conversions = XPConversion.get_user_conversions(user_id, limit=5)

        return {
            'xp': {
                'total': xp_total,
                'available': xp_available,
                'converted': xp_converted,
                'level': user.level
            },
            'credits': {
                'total': credits_total,
                'expiring_soon': credits_expiring,
                'wallets': [{
                    'id': w.id,
                    'remaining': w.credits_remaining,
                    'initial': w.credits_initial,
                    'expires_at': w.expires_at.strftime('%d/%m/%Y'),
                    'days_until_expiry': w.days_until_expiry,
                    'source': w.source_description
                } for w in wallets]
            },
            'recent_conversions': [{
                'id': c.id,
                'xp_spent': c.xp_spent,
                'credits_granted': c.credits_granted,
                'date': c.converted_at.strftime('%d/%m/%Y %H:%M'),
                'rule_name': c.rule.name if c.rule else 'N/A'
            } for c in conversions]
        }


# Singleton
credit_service = CreditService()
