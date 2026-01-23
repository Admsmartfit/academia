# app/utils/scheduler.py

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
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

    # Iniciar scheduler
    scheduler.start()
    print("[SCHEDULER] Iniciado com sucesso!")

    # Parar scheduler ao encerrar aplicacao
    atexit.register(lambda: scheduler.shutdown())


def get_scheduler():
    """Retorna instancia do scheduler"""
    return scheduler
