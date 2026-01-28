# app/utils/scheduler.py

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta
import atexit

scheduler = BackgroundScheduler()


def init_scheduler(app):
    """
    Inicializa o scheduler com contexto da aplicacao Flask
    """

    # Processar pagamentos atrasados (diario as 9h)
    @scheduler.scheduled_job(CronTrigger(hour=9, minute=0))
    def daily_payment_processing():
        with app.app_context():
            print(f"[SCHEDULER] Processando pagamentos atrasados...")
            from app.services.payment_processor import PaymentProcessor
            PaymentProcessor.process_overdue_payments()
            PaymentProcessor.expire_old_credits()

    # Lembretes de pagamento (diario as 10h)
    @scheduler.scheduled_job(CronTrigger(hour=10, minute=0))
    def daily_payment_reminders():
        with app.app_context():
            print(f"[SCHEDULER] Enviando lembretes de pagamento...")
            from app.services.payment_processor import PaymentProcessor
            PaymentProcessor.send_upcoming_payment_reminders()

    # Lembretes de aula 2h antes (a cada 30min)
    @scheduler.scheduled_job(IntervalTrigger(minutes=30))
    def class_reminders_2h():
        with app.app_context():
            from datetime import datetime, timedelta, time
            from app.models import Booking, BookingStatus
            from app import db

            now = datetime.now()
            two_hours_later = now + timedelta(hours=2)

            bookings = Booking.query.filter(
                Booking.date == two_hours_later.date(),
                Booking.status == BookingStatus.CONFIRMED,
                Booking.reminder_2h_sent == False
            ).all()

            # Filtrar por horario (dentro da janela de 30min)
            window_start = two_hours_later.time()
            window_end = (two_hours_later + timedelta(minutes=30)).time()

            for booking in bookings:
                schedule_time = booking.schedule.start_time
                if window_start <= schedule_time <= window_end:
                    try:
                        from app.services.megaapi import megaapi

                        # Preparar menu interativo
                        sections = [
                            {
                                "title": "Gerenciar Aula",
                                "rows": [
                                    {
                                        "title": "Confirmar Presenca",
                                        "rowId": f"confirm_{booking.id}",
                                        "description": "Garante sua vaga"
                                    },
                                    {
                                        "title": "Cancelar Aula",
                                        "rowId": f"cancel_{booking.id}",
                                        "description": "Libera vaga p/ outro"
                                    }
                                ]
                            }
                        ]

                        instructor_name = booking.schedule.instructor.name if booking.schedule.instructor else 'Instrutor'

                        text = f"""Ola {booking.user.name.split()[0]}!

Lembrete: Sua aula de *{booking.schedule.modality.name}* e daqui a 2 horas!

Data: {booking.date.strftime('%d/%m/%Y')}
Horario: {booking.schedule.start_time.strftime('%H:%M')}
Instrutor: {instructor_name}"""

                        megaapi.send_list_message(
                            phone=booking.user.phone,
                            text=text,
                            button_text="Opcoes",
                            sections=sections,
                            user_id=booking.user_id
                        )

                        booking.reminder_2h_sent = True
                    except Exception as e:
                        print(f"Erro ao enviar lembrete 2h: {e}")

            db.session.commit()

    # Lembretes de aula 24h antes (diario as 18h)
    @scheduler.scheduled_job(CronTrigger(hour=18, minute=0))
    def class_reminders_24h():
        with app.app_context():
            from datetime import datetime, timedelta
            from app.models import Booking, BookingStatus
            from app import db

            tomorrow = datetime.now() + timedelta(days=1)

            bookings = Booking.query.filter(
                Booking.date == tomorrow.date(),
                Booking.status == BookingStatus.CONFIRMED,
                Booking.reminder_24h_sent == False
            ).all()

            for booking in bookings:
                try:
                    from app.services.megaapi import megaapi

                    megaapi.send_template_message(
                        phone=booking.user.phone,
                        template_name='lembrete_aula_24h',
                        variables=[
                            booking.user.name.split()[0],
                            tomorrow.strftime('%d/%m'),
                            booking.schedule.start_time.strftime('%H:%M'),
                            booking.schedule.modality.name,
                            booking.schedule.instructor.name if booking.schedule.instructor else 'Instrutor',
                            'Academia Fitness'
                        ],
                        user_id=booking.user_id
                    )

                    booking.reminder_24h_sent = True
                except Exception as e:
                    print(f"Erro ao enviar lembrete 24h: {e}")

            db.session.commit()

    # Verificar conquistas (a cada hora)
    @scheduler.scheduled_job(IntervalTrigger(hours=1))
    def check_achievements():
        with app.app_context():
            print(f"[SCHEDULER] Verificando conquistas...")
            from app.services.achievement_checker import AchievementChecker
            AchievementChecker.check_all_users()

    # Criar agendamentos recorrentes (diario a meia-noite)
    @scheduler.scheduled_job(CronTrigger(hour=0, minute=0))
    def create_recurring_bookings():
        with app.app_context():
            from app.models import RecurringBooking
            from datetime import datetime

            print(f"[SCHEDULER] Processando agendamentos recorrentes...")

            today = datetime.now().date()

            # Buscar recorrencias ativas com proxima ocorrencia = hoje
            recurring = RecurringBooking.query.filter(
                RecurringBooking.is_active == True,
                RecurringBooking.next_occurrence == today
            ).all()

            created_count = 0
            for rec in recurring:
                try:
                    booking = rec.create_next_booking()
                    if booking:
                        created_count += 1
                except Exception as e:
                    print(f"Erro ao criar booking recorrente: {e}")

            print(f"[SCHEDULER] Criados {created_count} agendamentos recorrentes")

    # Processar recorrencias futuras (diario as 6h)
    @scheduler.scheduled_job(CronTrigger(hour=6, minute=0))
    def process_future_recurring():
        with app.app_context():
            print(f"[SCHEDULER] Processando recorrencias futuras...")
            from app.models import RecurringBooking
            RecurringBooking.process_all_recurring()

    # Backup diario do banco de dados (as 3h da manha)
    @scheduler.scheduled_job(CronTrigger(hour=3, minute=0))
    def daily_backup():
        with app.app_context():
            print("[SCHEDULER] Iniciando backup do banco de dados...")
            from app.utils.backup import backup_database
            backup_database()

    # Expirar creditos (diario as 0h30)
    @scheduler.scheduled_job(CronTrigger(hour=0, minute=30))
    def expire_credit_wallets():
        with app.app_context():
            print("[SCHEDULER] Expirando carteiras de credito...")
            from app.services.credit_service import CreditService
            from app.services.notification_service import NotificationService
            from app.models.credit_wallet import CreditWallet
            from app.models import User
            from app import db

            # Coleta informacoes antes de expirar para notificar
            now = datetime.now()
            expiring_today = CreditWallet.query.filter(
                CreditWallet.is_expired == False,
                CreditWallet.expires_at <= now,
                CreditWallet.credits_remaining > 0
            ).all()

            # Agrupa por usuario para notificar
            user_expired = {}
            for wallet in expiring_today:
                if wallet.user_id not in user_expired:
                    user_expired[wallet.user_id] = 0
                user_expired[wallet.user_id] += wallet.credits_remaining

            # Expira as carteiras
            count = CreditService.expire_wallets()

            # Notifica usuarios sobre creditos expirados
            for user_id, credits in user_expired.items():
                try:
                    NotificationService.notify_credits_expired(user_id, credits)
                except Exception as e:
                    print(f"[SCHEDULER] Erro ao notificar expiracao usuario {user_id}: {e}")

            print(f"[SCHEDULER] {count} carteiras expiradas")

    # Alerta de creditos expirando em 7 dias (diario as 11h)
    @scheduler.scheduled_job(CronTrigger(hour=11, minute=0))
    def notify_credits_expiring_7d():
        with app.app_context():
            print("[SCHEDULER] Enviando alertas de creditos expirando (7 dias)...")
            from app.models.credit_wallet import CreditWallet
            from app.services.notification_service import NotificationService
            from datetime import timedelta

            # Busca usuarios com creditos expirando em 7 dias
            seven_days = datetime.now() + timedelta(days=7)

            # Agrupa por usuario
            wallets = CreditWallet.query.filter(
                CreditWallet.is_expired == False,
                CreditWallet.credits_remaining > 0,
                CreditWallet.expires_at <= seven_days,
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
                # Notifica apenas se tem quantidade significativa (>= 1 credito)
                if info['credits'] >= 1:
                    try:
                        NotificationService.notify_credits_expiring(
                            user_id=user_id,
                            credits_amount=info['credits'],
                            days_remaining=info['days'],
                            expires_at=info['earliest_expiry']
                        )
                        count += 1
                    except Exception as e:
                        print(f"[SCHEDULER] Erro ao notificar usuario {user_id}: {e}")

            print(f"[SCHEDULER] {count} alertas de creditos expirando enviados")

    # Alerta de creditos expirando AMANHA (diario as 20h)
    @scheduler.scheduled_job(CronTrigger(hour=20, minute=0))
    def notify_credits_expiring_1d():
        with app.app_context():
            print("[SCHEDULER] Enviando alertas URGENTES de creditos expirando amanha...")
            from app.models.credit_wallet import CreditWallet
            from app.services.notification_service import NotificationService
            from datetime import timedelta

            # Creditos que expiram amanha
            tomorrow_start = (datetime.now() + timedelta(days=1)).replace(hour=0, minute=0, second=0)
            tomorrow_end = tomorrow_start + timedelta(days=1)

            wallets = CreditWallet.query.filter(
                CreditWallet.is_expired == False,
                CreditWallet.credits_remaining > 0,
                CreditWallet.expires_at >= tomorrow_start,
                CreditWallet.expires_at < tomorrow_end
            ).all()

            user_expiring = {}
            for wallet in wallets:
                if wallet.user_id not in user_expiring:
                    user_expiring[wallet.user_id] = {
                        'credits': 0,
                        'expires_at': wallet.expires_at
                    }
                user_expiring[wallet.user_id]['credits'] += wallet.credits_remaining

            count = 0
            for user_id, info in user_expiring.items():
                if info['credits'] >= 1:
                    try:
                        NotificationService.notify_credits_expiring(
                            user_id=user_id,
                            credits_amount=info['credits'],
                            days_remaining=1,
                            expires_at=info['expires_at']
                        )
                        count += 1
                    except Exception as e:
                        print(f"[SCHEDULER] Erro ao notificar usuario {user_id}: {e}")

            print(f"[SCHEDULER] {count} alertas urgentes enviados")

    # Verificar expiracao de PAR-Q (diario as 12h)
    @scheduler.scheduled_job(CronTrigger(hour=12, minute=0))
    def daily_health_screening_check():
        with app.app_context():
            print("[SCHEDULER] Verificando expiracao de triagens de saúde...")
            from app.models.health import HealthScreening, ScreeningStatus
            from app.services.notification_service import NotificationService
            from datetime import datetime, timedelta
            from app import db

            now = datetime.utcnow()
            
            # 1. Notificar quem expira em 7 dias
            expiring_7d = now + timedelta(days=7)
            # Simplificando a busca: screenings APTO que expiram entre hoje e 7 dias
            screenings_7d = HealthScreening.query.filter(
                HealthScreening.status == ScreeningStatus.APTO,
                HealthScreening.expires_at <= expiring_7d,
                HealthScreening.expires_at > now,
                HealthScreening.reminder_sent == False # Adicionando flag se possível ou filtrando por data exata
            ).all()
            
            # 2. Marcar como EXPIRADO quem ja passou da data
            expired = HealthScreening.query.filter(
                HealthScreening.status == ScreeningStatus.APTO,
                HealthScreening.expires_at <= now
            ).all()
            
            for s in expired:
                s.status = ScreeningStatus.EXPIRADO
                print(f"[SCHEDULER] PAR-Q de {s.user.name} expirado")
            
            db.session.commit()

            # 3. Notificacoes (simplificado)
            print(f"[SCHEDULER] {len(expired)} triagens marcadas como expiradas")

    # Lembrete de Hidratação Eletrolipólise (a cada 15min)
    @scheduler.scheduled_job(IntervalTrigger(minutes=15))
    def hydration_reminder_eletrolipo():
        with app.app_context():
            from app.models import Booking, BookingStatus
            from app.services.megaapi import megaapi
            from datetime import datetime, timedelta

            # Buscar aulas de Eletrolipólise começando nos próximos 30-45min
            now = datetime.now()
            window_start = now + timedelta(minutes=30)
            window_end = now + timedelta(minutes=45)
            
            # Precisamos filtrar por modalidade. Como modalidade está na ClassSchedule, fazemos join.
            # Assumimos que o nome contém "Eletrolipo"
            bookings = Booking.query.join(Booking.schedule).filter(
                Booking.status == BookingStatus.CONFIRMED,
                Booking.date == now.date(), # Apenas hoje
                Booking.schedule.has(ClassSchedule.modality.has(lambda m: m.name.like('%Eletrolipo%'))),
                Booking.reminder_hydration_sent == False
            ).all()

            # Precisamos filtrar horário pythonicamente pois Booking.schedule.start_time é Time
            for booking in bookings:
                booking_dt = datetime.combine(booking.date, booking.schedule.start_time)
                if window_start <= booking_dt <= window_end:
                    try:
                        first_name = booking.user.name.split()[0]
                        msg = (f"Olá {first_name}! 💧\n\n"
                               f"Sua sessão de Eletrolipólise começa em 30min.\n"
                               f"Lembre-se de beber pelo menos 500ml de água agora para garantir o resultado! 🥤")
                        
                        megaapi.send_message(
                            phone=booking.user.phone,
                            message=msg,
                            user_id=booking.user_id
                        )
                        
                        booking.reminder_hydration_sent = True
                        print(f"[SCHEDULER] Lembrete hidratação enviado para {booking.user.name}")
                    except Exception as e:
                        print(f"[SCHEDULER] Erro ao enviar lembrete hidratação: {e}")
            
            db.session.commit()

    # Iniciar scheduler
    scheduler.start()
    print("[SCHEDULER] Iniciado com sucesso!")

    # Parar scheduler ao encerrar aplicacao
    atexit.register(lambda: scheduler.shutdown())


def get_scheduler():
    """Retorna instancia do scheduler"""
    return scheduler
