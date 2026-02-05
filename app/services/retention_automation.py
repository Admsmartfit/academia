from datetime import datetime, timedelta
from flask import current_app
from app.models import User, Booking, StudentHealthScore, Lead, AutomationLog
from app.services.megaapi import megaapi, Button, ListMessage, ListSection
from app import db
import logging

logger = logging.getLogger(__name__)

class RetentionAutomation:
    """
    Automações de retenção baseadas em réguas de relacionamento.
    
    Réguas implementadas:
    1. Boas-vindas (D+1)
    2. Engajamento (D+15)
    3. Recuperação Leve (Ausente 5 dias)
    4. Recuperação Crítica (Ausente 10 dias)
    5. Última Tentativa (Ausente 20 dias)
    """
    
    def __init__(self):
        # Usamos a instancia global megaapi importada
        pass
    
    def run_daily_automations(self):
        """
        Executa todas as automações diárias.
        Deve ser chamado via scheduler.
        """
        logger.info("Iniciando automações de retenção...")
        
        results = {
            'welcome_sent': 0,
            'engagement_sent': 0,
            'recovery_light_sent': 0,
            'recovery_critical_sent': 0,
            'last_attempt_sent': 0
        }
        
        # 1. Boas-vindas (usuários cadastrados ontem)
        results['welcome_sent'] = self.send_welcome_messages()
        
        # 2. Engajamento (usuários com 15 dias)
        results['engagement_sent'] = self.send_engagement_survey()
        
        # 3. Recuperação leve (5 dias sem check-in)
        results['recovery_light_sent'] = self.send_light_recovery()
        
        # 4. Recuperação crítica (10 dias sem check-in)
        results['recovery_critical_sent'] = self.send_critical_recovery()
        
        # 5. Última tentativa (20 dias sem check-in)
        results['last_attempt_sent'] = self.send_last_attempt()
        
        logger.info(f"Automações concluídas: {results}")
        return results
    
    def send_welcome_messages(self) -> int:
        """Mensagem de boas-vindas para novos alunos (D+1)."""
        yesterday = datetime.utcnow() - timedelta(days=1)
        # Janela de 24h a partir de ontem
        
        new_students = User.query.filter(
            User.role == 'student',
            User.created_at >= yesterday.replace(hour=0, minute=0, second=0),
            User.created_at <= yesterday.replace(hour=23, minute=59, second=59),
            User.phone.isnot(None),
            User.is_active == True
        ).all()
        
        sent_count = 0
        
        for student in new_students:
            try:
                # Verificar se ja enviou welcome
                existing = AutomationLog.query.filter_by(user_id=student.id, automation_type='WELCOME').first()
                if existing:
                    continue

                buttons = [
                    Button(id='facial_tutorial', title='📸 Como usar facial'),
                    Button(id='schedule_evaluation', title='📋 Agendar avaliação'),
                    Button(id='view_training', title='💪 Ver meu treino')
                ]
                
                message = f"""
Olá {student.name.split()[0]}! 🎉

Seja muito bem-vindo(a) à nossa academia! Estamos muito felizes em tê-lo(a) conosco.

Para aproveitar ao máximo sua experiência:

✅ Use o reconhecimento facial para check-in automático
✅ Acesse seu treino personalizado pelo celular
✅ Agende sua avaliação física gratuita

Escolha uma opção abaixo ou me mande uma mensagem se tiver dúvidas!
                """.strip()
                
                result = megaapi.send_buttons(
                    phone=student.phone,
                    message=message,
                    buttons=buttons,
                    user_id=student.id
                )
                
                if result.get('success'):
                    self._log_automation('WELCOME', student.id)
                    sent_count += 1
                    
            except Exception as e:
                logger.error(f"Erro ao enviar boas-vindas para {student.id}: {e}")
        
        return sent_count
    
    def send_engagement_survey(self) -> int:
        """Pesquisa de satisfação após 15 dias."""
        target_date = datetime.utcnow() - timedelta(days=15)
        
        students = User.query.filter(
            User.role == 'student',
            User.created_at >= target_date.replace(hour=0, minute=0, second=0),
            User.created_at <= target_date.replace(hour=23, minute=59, second=59),
            User.phone.isnot(None),
            User.is_active == True
        ).all()
        
        sent_count = 0
        
        for student in students:
            try:
                # Verificar se ja enviou survey
                existing = AutomationLog.query.filter_by(user_id=student.id, automation_type='ENGAGEMENT_SURVEY').first()
                if existing:
                    continue
                
                sections = [
                    {
                        "title": "Sua Avaliação",
                        "rows": [
                            {'id': 'satisfaction_5', 'title': '⭐⭐⭐⭐⭐', 'description': 'Excelente!'},
                            {'id': 'satisfaction_4', 'title': '⭐⭐⭐⭐', 'description': 'Muito bom'},
                            {'id': 'satisfaction_3', 'title': '⭐⭐⭐', 'description': 'Bom'},
                            {'id': 'satisfaction_2', 'title': '⭐⭐', 'description': 'Regular'},
                            {'id': 'satisfaction_1', 'title': '⭐', 'description': 'Insatisfeito'}
                        ]
                    }
                ]
                
                text = f"Olá {student.name.split()[0]}! Já faz 15 dias que você está conosco. Como você avalia sua experiência até agora?"
                
                result = megaapi.send_list_message(
                    phone=student.phone,
                    text=text,
                    button_text="Avaliar",
                    sections=sections,
                    user_id=student.id
                )
                
                if result.get('success'):
                    self._log_automation('ENGAGEMENT_SURVEY', student.id)
                    sent_count += 1
                    
            except Exception as e:
                logger.error(f"Erro ao enviar pesquisa para {student.id}: {e}")
        
        return sent_count
    
    def send_light_recovery(self) -> int:
        """Recuperação leve: 5 dias sem check-in."""
        five_days_ago = datetime.utcnow() - timedelta(days=5)
        
        # Alunos ativos que não tiveram check-in nos ultimos 5 dias 
        # e o ultimo check-in foi exatamente ha 5 dias (para evitar reenvio manual diario se nao fizermos controle fino)
        # Melhor usar AutomationLog para nao repetir.
        
        students_absent = db.session.query(User).filter(
            User.role == 'student',
            User.is_active == True,
            User.phone.isnot(None)
        ).all()
        
        sent_count = 0
        
        for student in students_absent:
            # Pegar ultimo checkin
            from app.models.booking import Booking
            last_booking = Booking.query.filter(
                Booking.user_id == student.id,
                Booking.status == 'COMPLETED'
            ).order_by(Booking.checked_in_at.desc()).first()
            
            if not last_booking or not last_booking.checked_in_at:
                continue
                
            days_absent = (datetime.utcnow() - last_booking.checked_in_at).days
            
            if days_absent == 5:
                # Verificar log recente
                if self._sent_recovery_recently(student.id, days=3):
                    continue
                
                try:
                    buttons = [
                        Button(id='yes_tomorrow', title='✅ Vou amanhã!'),
                        Button(id='reschedule_me', title='📅 Reagendar'),
                        Button(id='im_ok', title='😊 Está tudo bem')
                    ]
                    
                    message = f"""
Olá {student.name.split()[0]}! 

Sentimos sua falta por aqui! Faz 5 dias que você não vem treinar. 

Sabemos que a rotina é corrida, mas lembre-se: cada treino te deixa mais perto dos seus objetivos! 💪

Quando podemos te esperar?
                    """.strip()
                    
                    result = megaapi.send_buttons(
                        phone=student.phone,
                        message=message,
                        buttons=buttons,
                        user_id=student.id
                    )
                    
                    if result.get('success'):
                        self._log_automation('RECOVERY_LIGHT', student.id)
                        sent_count += 1
                        
                except Exception as e:
                    logger.error(f"Erro em recuperação leve para {student.id}: {e}")
        
        return sent_count
    
    def send_critical_recovery(self) -> int:
        """Recuperação crítica: 10 dias sem check-in."""
        ten_days_ago = datetime.utcnow() - timedelta(days=10)
        
        students_critical = db.session.query(User).filter(
            User.role == 'student',
            User.is_active == True,
            User.phone.isnot(None)
        ).all()
        
        sent_count = 0
        
        for student in students_critical:
            from app.models.booking import Booking
            last_booking = Booking.query.filter(
                Booking.user_id == student.id,
                Booking.status == 'COMPLETED'
            ).order_by(Booking.checked_in_at.desc()).first()
            
            if not last_booking or not last_booking.checked_in_at:
                continue
                
            days_absent = (datetime.utcnow() - last_booking.checked_in_at).days
            
            if days_absent == 10:
                if self._sent_recovery_recently(student.id, days=5):
                    continue
                
                try:
                    buttons = [
                        Button(id='talk_to_instructor', title='💬 Falar com instrutor'),
                        Button(id='free_personal', title='🎁 Sessão grátis'),
                        Button(id='schedule_now', title='📅 Agendar agora')
                    ]
                    
                    message = f"""
{student.name.split()[0]}, aqui é da equipe da academia! 

Notei que você não está vindo treinar. Tudo bem com você?

Quero te ajudar a voltar com tudo! Que tal uma sessão gratuita de personal para te motivar?

Conte conosco! 💪❤️
                    """.strip()
                    
                    result = megaapi.send_buttons(
                        phone=student.phone,
                        message=message,
                        buttons=buttons,
                        user_id=student.id
                    )
                    
                    if result.get('success'):
                        self._log_automation('RECOVERY_CRITICAL', student.id)
                        sent_count += 1
                        
                except Exception as e:
                    logger.error(f"Erro em recuperação crítica para {student.id}: {e}")
        
        return sent_count
    
    def send_last_attempt(self) -> int:
        """Última tentativa: 20 dias sem check-in + desconto."""
        twenty_days_ago = datetime.utcnow() - timedelta(days=20)
        
        students_last = db.session.query(User).filter(
            User.role == 'student',
            User.is_active == True,
            User.phone.isnot(None)
        ).all()
        
        sent_count = 0
        
        for student in students_last:
            from app.models.booking import Booking
            last_booking = Booking.query.filter(
                Booking.user_id == student.id,
                Booking.status == 'COMPLETED'
            ).order_by(Booking.checked_in_at.desc()).first()
            
            if not last_booking or not last_booking.checked_in_at:
                continue
                
            days_absent = (datetime.utcnow() - last_booking.checked_in_at).days
            
            if days_absent == 20:
                if self._sent_recovery_recently(student.id, days=10):
                    continue

                try:
                    buttons = [
                        Button(id='claim_discount', title='💰 Quero o desconto'),
                        Button(id='schedule_call', title='📞 Agendar ligação'),
                        Button(id='cancel_membership', title='😢 Cancelar matrícula')
                    ]
                    
                    message = f"""
{student.name.split()[0]}, queremos MUITO você de volta! 😊

Preparamos uma condição ESPECIAL só para você:

🎁 30% DE DESCONTO no próximo mês
🎁 1 mês de personal trainer grátis

Sua saúde e bem-estar são nossa prioridade! Volte a treinar hoje mesmo! 💪
                    """.strip()
                    
                    result = megaapi.send_buttons(
                        phone=student.phone,
                        message=message,
                        buttons=buttons,
                        user_id=student.id
                    )
                    
                    if result.get('success'):
                        self._log_automation('LAST_ATTEMPT', student.id)
                        sent_count += 1
                        
                except Exception as e:
                    logger.error(f"Erro em última tentativa para {student.id}: {e}")
        
        return sent_count
    
    # ================= MÉTODOS AUXILIARES =================
    
    def _log_automation(self, automation_type: str, user_id: int):
        """Registra envio de automação."""
        try:
            log = AutomationLog(
                user_id=user_id,
                automation_type=automation_type,
                sent_at=datetime.utcnow()
            )
            db.session.add(log)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao logar automação: {e}")
    
    def _sent_recovery_recently(self, user_id: int, days: int) -> bool:
        """Verifica se já enviou mensagem de recuperação recentemente."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        recent_log = AutomationLog.query.filter(
            AutomationLog.user_id == user_id,
            AutomationLog.automation_type.in_(['RECOVERY_LIGHT', 'RECOVERY_CRITICAL', 'LAST_ATTEMPT']),
            AutomationLog.sent_at >= cutoff
        ).first()
        
        return recent_log is not None
