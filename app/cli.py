# app/cli.py

import click
from flask.cli import with_appcontext


def register_cli_commands(app):
    """Registra comandos CLI no app Flask"""

    @app.cli.group()
    def credits():
        """Comandos para gerenciamento de creditos"""
        pass

    @credits.command('expire')
    @with_appcontext
    def expire_credits():
        """Expira carteiras de credito vencidas"""
        from app.services.credit_service import CreditService

        click.echo("Expirando carteiras de credito...")
        count = CreditService.expire_wallets()
        click.echo(f"Total de {count} carteiras expiradas.")

    @credits.command('notify-expiring')
    @click.option('--days', default=7, help='Dias ate expiracao')
    @with_appcontext
    def notify_expiring_credits(days):
        """Notifica usuarios sobre creditos expirando"""
        from datetime import datetime, timedelta
        from app.models.credit_wallet import CreditWallet
        from app.services.notification_service import NotificationService

        click.echo(f"Buscando creditos expirando em {days} dias...")

        target_date = datetime.now() + timedelta(days=days)

        wallets = CreditWallet.query.filter(
            CreditWallet.is_expired == False,
            CreditWallet.credits_remaining > 0,
            CreditWallet.expires_at <= target_date,
            CreditWallet.expires_at > datetime.now()
        ).all()

        user_expiring = {}
        for wallet in wallets:
            if wallet.user_id not in user_expiring:
                user_expiring[wallet.user_id] = {
                    'credits': 0,
                    'earliest_expiry': wallet.expires_at,
                    'days': wallet.days_until_expiry
                }
            user_expiring[wallet.user_id]['credits'] += wallet.credits_remaining
            if wallet.expires_at < user_expiring[wallet.user_id]['earliest_expiry']:
                user_expiring[wallet.user_id]['earliest_expiry'] = wallet.expires_at
                user_expiring[wallet.user_id]['days'] = wallet.days_until_expiry

        count = 0
        for user_id, info in user_expiring.items():
            if info['credits'] >= 1:
                try:
                    NotificationService.notify_credits_expiring(
                        user_id=user_id,
                        credits_amount=info['credits'],
                        days_remaining=info['days'],
                        expires_at=info['earliest_expiry']
                    )
                    count += 1
                    click.echo(f"  - Usuario {user_id}: {info['credits']} creditos expirando")
                except Exception as e:
                    click.echo(f"  - Erro usuario {user_id}: {e}")

        click.echo(f"Total de {count} notificacoes enviadas.")

    @app.cli.group()
    def xp():
        """Comandos para gerenciamento de XP"""
        pass

    @xp.command('check-conversions')
    @click.option('--user-id', type=int, help='ID do usuario especifico')
    @with_appcontext
    def check_automatic_conversions(user_id):
        """Verifica e executa conversoes automaticas de XP"""
        from app.services.credit_service import CreditService
        from app.models import User

        if user_id:
            users = [User.query.get(user_id)]
            if not users[0]:
                click.echo(f"Usuario {user_id} nao encontrado.")
                return
        else:
            # Busca usuarios com XP disponivel
            from app.models.xp_ledger import XPLedger
            from sqlalchemy import func
            from datetime import datetime

            user_ids = XPLedger.query.filter(
                XPLedger.expires_at > datetime.utcnow(),
                XPLedger.xp_amount > XPLedger.converted_amount
            ).with_entities(XPLedger.user_id).distinct().all()

            users = User.query.filter(User.id.in_([u[0] for u in user_ids])).all()

        click.echo(f"Verificando conversoes para {len(users)} usuarios...")

        total_conversions = 0
        for user in users:
            if user:
                conversions = CreditService.check_automatic_conversions(user.id)
                if conversions:
                    click.echo(f"  - Usuario {user.id} ({user.name}): {len(conversions)} conversoes")
                    total_conversions += len(conversions)

        click.echo(f"Total de {total_conversions} conversoes realizadas.")

    @xp.command('summary')
    @click.argument('user_id', type=int)
    @with_appcontext
    def xp_summary(user_id):
        """Mostra resumo de XP e creditos de um usuario"""
        from app.services.credit_service import CreditService
        from app.models import User

        user = User.query.get(user_id)
        if not user:
            click.echo(f"Usuario {user_id} nao encontrado.")
            return

        summary = CreditService.get_user_summary(user_id)

        click.echo(f"\n=== Resumo: {user.name} ===\n")
        click.echo(f"XP Total (Ranking): {summary['xp']['total']}")
        click.echo(f"XP Disponivel para Conversao: {summary['xp']['available']}")
        click.echo(f"XP Ja Convertido: {summary['xp']['converted']}")
        click.echo(f"Nivel: {summary['xp']['level']}")
        click.echo(f"\nCreditos Totais: {summary['credits']['total']}")
        click.echo(f"Creditos Expirando (7 dias): {summary['credits']['expiring_soon']}")

        if summary['credits']['wallets']:
            click.echo("\nCarteiras de Credito:")
            for w in summary['credits']['wallets']:
                click.echo(f"  - {w['remaining']}/{w['initial']} cred | Expira: {w['expires_at']} | {w['source']}")

        if summary['recent_conversions']:
            click.echo("\nConversoes Recentes:")
            for c in summary['recent_conversions']:
                click.echo(f"  - {c['date']}: {c['xp_spent']} XP -> {c['credits_granted']} cred ({c['rule_name']})")

    @app.cli.group()
    def notifications():
        """Comandos para notificacoes"""
        pass

    @notifications.command('test')
    @click.argument('user_id', type=int)
    @click.argument('notification_type', type=click.Choice(['conversion', 'expiring', 'goal']))
    @with_appcontext
    def test_notification(user_id, notification_type):
        """Envia notificacao de teste para usuario"""
        from app.services.notification_service import NotificationService
        from app.models import User
        from datetime import datetime, timedelta

        user = User.query.get(user_id)
        if not user:
            click.echo(f"Usuario {user_id} nao encontrado.")
            return

        click.echo(f"Enviando notificacao de teste ({notification_type}) para {user.name}...")

        try:
            if notification_type == 'expiring':
                result = NotificationService.notify_credits_expiring(
                    user_id=user_id,
                    credits_amount=10,
                    days_remaining=5,
                    expires_at=datetime.now() + timedelta(days=5)
                )
            elif notification_type == 'goal':
                from app.models.conversion_rule import ConversionRule
                rule = ConversionRule.query.filter_by(is_active=True).first()
                if rule:
                    result = NotificationService.notify_xp_goal_near(
                        user_id=user_id,
                        xp_available=int(rule.xp_required * 0.85),
                        rule=rule
                    )
                else:
                    click.echo("Nenhuma regra de conversao encontrada.")
                    return
            else:
                click.echo("Tipo de notificacao de teste nao implementado.")
                return

            if result:
                click.echo("Notificacao enviada com sucesso!")
            else:
                click.echo("Falha ao enviar notificacao (template nao configurado?).")

        except Exception as e:
            click.echo(f"Erro: {e}")
