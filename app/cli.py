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

    @app.cli.command('seed-exercises')
    @with_appcontext
    def seed_exercises():
        """Popula banco com exercicios basicos"""
        from app import db
        from app.models.training import Exercise, MuscleGroup, DifficultyLevel

        exercises_data = [
            # Peito
            {'name': 'Supino Reto com Barra', 'muscle_group': MuscleGroup.CHEST,
             'difficulty_level': DifficultyLevel.INTERMEDIATE, 'equipment_needed': 'Barra, Banco reto',
             'description': 'Deite no banco reto, segure a barra na largura dos ombros e empurre para cima.'},
            {'name': 'Supino Inclinado com Halteres', 'muscle_group': MuscleGroup.CHEST,
             'difficulty_level': DifficultyLevel.INTERMEDIATE, 'equipment_needed': 'Halteres, Banco inclinado',
             'description': 'Deite no banco inclinado (45 graus) e empurre os halteres para cima.'},
            {'name': 'Crucifixo com Halteres', 'muscle_group': MuscleGroup.CHEST,
             'difficulty_level': DifficultyLevel.BEGINNER, 'equipment_needed': 'Halteres, Banco reto',
             'description': 'Deite no banco, abra os bracos lateralmente com os halteres e junte no alto.'},
            # Costas
            {'name': 'Puxada Frontal', 'muscle_group': MuscleGroup.BACK,
             'difficulty_level': DifficultyLevel.BEGINNER, 'equipment_needed': 'Pulley',
             'description': 'Segure a barra do pulley com pegada aberta e puxe ate o peito.'},
            {'name': 'Remada Curvada com Barra', 'muscle_group': MuscleGroup.BACK,
             'difficulty_level': DifficultyLevel.INTERMEDIATE, 'equipment_needed': 'Barra',
             'description': 'Incline o tronco, segure a barra e puxe em direcao ao abdomen.'},
            # Pernas
            {'name': 'Agachamento Livre', 'muscle_group': MuscleGroup.LEGS,
             'difficulty_level': DifficultyLevel.INTERMEDIATE, 'equipment_needed': 'Barra, Suporte',
             'description': 'Posicione a barra nos ombros e agache ate as coxas ficarem paralelas ao chao.'},
            {'name': 'Leg Press 45', 'muscle_group': MuscleGroup.LEGS,
             'difficulty_level': DifficultyLevel.BEGINNER, 'equipment_needed': 'Leg Press',
             'description': 'Sente na maquina, posicione os pes na plataforma e empurre.'},
            {'name': 'Cadeira Extensora', 'muscle_group': MuscleGroup.LEGS,
             'difficulty_level': DifficultyLevel.BEGINNER, 'equipment_needed': 'Cadeira Extensora',
             'description': 'Sente na maquina e estenda as pernas completamente.'},
            # Ombros
            {'name': 'Desenvolvimento com Halteres', 'muscle_group': MuscleGroup.SHOULDERS,
             'difficulty_level': DifficultyLevel.INTERMEDIATE, 'equipment_needed': 'Halteres',
             'description': 'Sentado, empurre os halteres acima da cabeca.'},
            {'name': 'Elevacao Lateral', 'muscle_group': MuscleGroup.SHOULDERS,
             'difficulty_level': DifficultyLevel.BEGINNER, 'equipment_needed': 'Halteres',
             'description': 'Em pe, eleve os halteres lateralmente ate a altura dos ombros.'},
            # Bracos
            {'name': 'Rosca Direta com Barra', 'muscle_group': MuscleGroup.ARMS,
             'difficulty_level': DifficultyLevel.BEGINNER, 'equipment_needed': 'Barra',
             'description': 'Em pe, segure a barra com pegada supinada e flexione os cotovelos.'},
            {'name': 'Triceps Pulley', 'muscle_group': MuscleGroup.ARMS,
             'difficulty_level': DifficultyLevel.BEGINNER, 'equipment_needed': 'Pulley, Barra reta',
             'description': 'No pulley, empurre a barra para baixo estendendo os cotovelos.'},
            # Core
            {'name': 'Abdominal Crunch', 'muscle_group': MuscleGroup.CORE,
             'difficulty_level': DifficultyLevel.BEGINNER, 'equipment_needed': 'Colchonete',
             'description': 'Deite com joelhos flexionados e eleve o tronco em direcao aos joelhos.'},
            {'name': 'Prancha Isometrica', 'muscle_group': MuscleGroup.CORE,
             'difficulty_level': DifficultyLevel.BEGINNER, 'equipment_needed': 'Colchonete',
             'description': 'Apoie-se nos antebracos e pontas dos pes, mantendo o corpo reto.'},
            # Corpo Inteiro
            {'name': 'Burpee', 'muscle_group': MuscleGroup.FULL_BODY,
             'difficulty_level': DifficultyLevel.ADVANCED, 'equipment_needed': 'Nenhum',
             'description': 'Agache, coloque as maos no chao, pule para posicao de flexao, volte e salte.'},
        ]

        created = 0
        skipped = 0
        for data in exercises_data:
            existing = Exercise.query.filter_by(name=data['name']).first()
            if existing:
                skipped += 1
                continue
            exercise = Exercise(**data)
            db.session.add(exercise)
            created += 1

        db.session.commit()
        click.echo(f"Seed concluido: {created} exercicios criados, {skipped} ja existiam.")

    @app.cli.command('calculate-scores')
    @with_appcontext
    def calculate_scores():
        """Calcula health scores de todos os alunos"""
        from app.services.health_score_calculator import HealthScoreCalculator
        click.echo("Iniciando cálculo de health scores...")
        calculator = HealthScoreCalculator()
        results = calculator.calculate_all_students()
        click.echo(f"Concluído: {results['total']} processados, {results['updated']} atualizados, {results['critical']} críticos, {results['high_risk']} alto risco.")

    @app.cli.command('run-automations')
    @with_appcontext
    def run_automations():
        """Executa réguas de relacionamento/automações de retenção"""
        from app.services.retention_automation import RetentionAutomation
        click.echo("Executando automações de retenção...")
        automation = RetentionAutomation()
        results = automation.run_daily_automations()
        click.echo(f"Concluído: {results}")
