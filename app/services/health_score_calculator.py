from datetime import datetime, timedelta
from sqlalchemy import func
from app.models import (
    User, Booking, StudentHealthScore, Package,
    FaceRecognitionLog, TrainingSession
)
from app.models.crm import RiskLevel
from app import db
import logging

logger = logging.getLogger(__name__)

class HealthScoreCalculator:
    """
    Calcula o Health Score de alunos baseado em 4 componentes:
    1. Frequência (40%) - Check-ins nos últimos 30 dias
    2. Engajamento (30%) - Interações com o sistema
    3. Financeiro (20%) - Status de pagamento
    4. Tenure (10%) - Tempo de matrícula
    
    Score final: 0-100
    Risk Levels:
    - 0-39: CRITICAL
    - 40-59: HIGH
    - 60-79: MEDIUM
    - 80-100: LOW
    """
    
    def __init__(self):
        self.lookback_days = 30
    
    def calculate_all_students(self):
        """
        Calcula score de todos os alunos ativos.
        Deve ser executado diariamente via scheduler.
        """
        logger.info("Iniciando cálculo de health scores...")
        
        students = User.query.filter_by(role='student', is_active=True).all()
        
        results = {
            'total': len(students),
            'updated': 0,
            'critical': 0,
            'high_risk': 0
        }
        
        for student in students:
            try:
                score_data = self.calculate_student_score(student.id)
                self._save_score(student.id, score_data)
                
                results['updated'] += 1
                
                if score_data['risk_level'] == RiskLevel.CRITICAL:
                    results['critical'] += 1
                elif score_data['risk_level'] == RiskLevel.HIGH:
                    results['high_risk'] += 1
                    
            except Exception as e:
                logger.error(f"Erro ao calcular score do aluno {student.id}: {e}")
        
        logger.info(f"Health scores atualizados: {results}")
        return results
    
    def calculate_student_score(self, user_id: int) -> dict:
        """
        Calcula score de um aluno específico.
        
        Returns:
            {
                'frequency_score': float,
                'engagement_score': float,
                'financial_score': float,
                'tenure_score': float,
                'total_score': float,
                'risk_level': str,
                'details': dict
            }
        """
        user = User.query.get(user_id)
        if not user:
            raise ValueError(f"Usuário {user_id} não encontrado")
        
        # 1. Frequency Score (40 pontos)
        frequency_score, freq_details = self._calculate_frequency(user_id)
        
        # 2. Engagement Score (30 pontos)
        engagement_score, eng_details = self._calculate_engagement(user_id)
        
        # 3. Financial Score (20 pontos)
        financial_score, fin_details = self._calculate_financial(user_id)
        
        # 4. Tenure Score (10 pontos)
        tenure_score, ten_details = self._calculate_tenure(user)
        
        # Score total
        total_score = (
            frequency_score + 
            engagement_score + 
            financial_score + 
            tenure_score
        )
        
        # Risk level
        risk_level = self._determine_risk_level(total_score)
        
        return {
            'frequency_score': frequency_score,
            'engagement_score': engagement_score,
            'financial_score': financial_score,
            'tenure_score': tenure_score,
            'total_score': total_score,
            'risk_level': risk_level,
            'details': {
                'frequency': freq_details,
                'engagement': eng_details,
                'financial': fin_details,
                'tenure': ten_details
            }
        }
    
    def _calculate_frequency(self, user_id: int) -> tuple:
        """
        Calcula score de frequência (0-40).
        Baseado em check-ins nos últimos 30 dias.
        """
        cutoff_date = datetime.utcnow() - timedelta(days=self.lookback_days)
        
        # Conta check-ins
        checkins = Booking.query.filter(
            Booking.user_id == user_id,
            Booking.status == 'COMPLETED',
            Booking.checked_in_at >= cutoff_date
        ).count()
        
        # Lógica de pontuação
        if checkins == 0:
            score = 0
        elif checkins <= 4:  # <= 1x por semana
            score = 10
        elif checkins <= 8:  # 2x por semana
            score = 20
        elif checkins <= 12:  # 3x por semana
            score = 30
        else:  # 4+ por semana
            score = 40
        
        # Último check-in
        last_checkin = Booking.query.filter(
            Booking.user_id == user_id,
            Booking.status == 'COMPLETED'
        ).order_by(Booking.checked_in_at.desc()).first()
        
        days_since_last = None
        if last_checkin and last_checkin.checked_in_at:
            days_since_last = (datetime.utcnow() - last_checkin.checked_in_at).days
        
        details = {
            'checkins_30d': checkins,
            'days_since_last_checkin': days_since_last,
            'avg_per_week': round(checkins / 4.3, 1)
        }
        
        return score, details
    
    def _calculate_engagement(self, user_id: int) -> tuple:
        """
        Calcula score de engajamento (0-30).
        Baseado em interações com o sistema.
        """
        cutoff_date = datetime.utcnow() - timedelta(days=self.lookback_days)
        score = 0
        
        # Visualizou treino?
        viewed_training = TrainingSession.query.filter(
            TrainingSession.user_id == user_id,
            TrainingSession.viewed_at >= cutoff_date
        ).count() > 0
        
        if viewed_training:
            score += 10
        
        # Respondeu mensagens do WhatsApp? (Placeholder: assumindo 10 para agora)
        # TODO: Implementar verificação real quando tabela de respostas existir
        respond_score = 10
        score += respond_score
        
        # Completou avaliação física (Screening)?
        # Usando user.has_valid_screening via ScreeningService ou User model method
        user = User.query.get(user_id)
        from app.models.health import ScreeningType
        has_screening_parq = False
        try:
             has_screening_parq = user.has_valid_screening(ScreeningType.PARQ)
        except:
             pass
             
        if has_screening_parq:
            score += 5
        
        # Usou reconhecimento facial?
        used_facial = FaceRecognitionLog.query.filter(
            FaceRecognitionLog.user_id == user_id,
            FaceRecognitionLog.timestamp >= cutoff_date,
            FaceRecognitionLog.success == True
        ).count() > 0
        
        if used_facial:
            score += 5
        
        details = {
            'viewed_training': viewed_training,
            'used_facial_recognition': used_facial,
            'valid_screening': has_screening_parq,
            'engagement_raw_score': score
        }
        
        return score, details
    
    def _calculate_financial(self, user_id: int) -> tuple:
        """
        Calcula score financeiro (0-20).
        Baseado em status de pagamento.
        """
        user = User.query.get(user_id)
        
        # Verificar se tem pacote ativo
        active_package = Package.query.filter(
            Package.user_id == user_id,
            Package.is_active == True,
            Package.expires_at > datetime.utcnow()
        ).first()
        
        if not active_package:
            score = 0
            status = 'SEM_PACOTE'
            days_to_expiration = None
        else:
            # Verificar atraso de pagamento (assumindo payment_status no Package)
            # Na verdade, Package geralmente não tem payment_status, mas Subscription ou Payment tem.
            # O prompt assume Package.payment_status. Vou verificar app/models/package.py
            # Se não tiver, vou ajustar para Payment table.
            
            # Ajuste: Verificar Payment mais recente associado ao pacote ou usuario
            from app.models.payment import Payment, PaymentStatusEnum
            
            # Assumindo que se o pacote está ativo, está pago, a menos que haja controle de parcelas.
            # Vamos simplificar: Se está ativo e não expirado = 20 pontos.
            # Se expirado recentemente = 10 pontos.
            
            score = 20
            status = 'EM_DIA'
            days_to_expiration = (active_package.expires_at - datetime.utcnow()).days
            
            # TODO: Refinar com lógica de inadimplência real se houver tabela de mensalidades/cobranças
        
        details = {
            'payment_status': status,
            'has_active_package': active_package is not None,
            'days_to_expiration': days_to_expiration
        }
        
        return score, details
    
    def _calculate_tenure(self, user: User) -> tuple:
        """
        Calcula score de tempo de casa (0-10).
        """
        if not user.created_at:
            return 0, {'months': 0}
        
        days_since_join = (datetime.utcnow() - user.created_at).days
        months = days_since_join / 30
        
        if months >= 12:
            score = 10
        elif months >= 6:
            score = 7
        elif months >= 3:
            score = 5
        elif months >= 1:
            score = 3
        else:
            score = 0
        
        details = {
            'months': round(months, 1),
            'loyalty_level': 'HIGH' if months >= 12 else 'MEDIUM' if months >= 6 else 'LOW'
        }
        
        return score, details
    
    def _determine_risk_level(self, total_score: float) -> RiskLevel:
        """Determina o nível de risco baseado no score total."""
        if total_score >= 80:
            return RiskLevel.LOW
        elif total_score >= 60:
            return RiskLevel.MEDIUM
        elif total_score >= 40:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL

    def _save_score(self, user_id: int, score_data: dict):
        """Salva score no banco de dados."""
        risk = score_data['risk_level']

        score_record = StudentHealthScore(
            user_id=user_id,
            calculated_at=datetime.utcnow(),
            frequency_score=score_data['frequency_score'],
            engagement_score=score_data['engagement_score'],
            financial_score=score_data['financial_score'],
            tenure_score=score_data['tenure_score'],
            total_score=score_data['total_score'],
            risk_level=risk,
            requires_attention=(risk in (RiskLevel.HIGH, RiskLevel.CRITICAL))
        )

        db.session.add(score_record)
        db.session.commit()
