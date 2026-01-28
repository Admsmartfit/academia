from datetime import datetime
from app.models.health import ScreeningStatus, ScreeningType, EMSSessionLog

class ScreeningService:
    
    @staticmethod
    def validate_parq_responses(responses):
        """
        Valida respostas do PAR-Q.
        Retorna ScreeningStatus.PENDENTE_MEDICO se houver qualquer "SIM" (True),
        caso contrário retorna ScreeningStatus.APTO.
        """
        has_yes = any(responses.values())
        
        if has_yes:
            return ScreeningStatus.PENDENTE_MEDICO
        return ScreeningStatus.APTO
    
    @staticmethod
    def validate_ems_responses(responses):
        """
        Valida respostas da anamnese EMS.
        Q1, Q2, Q3: Contraindicações absolutas (BLOQUEADO)
        Q4-Q7: Contraindicações relativas (PENDENTE_MEDICO)
        """
        # Q1, Q2, Q3: Contraindicações absolutas
        absolute_contraindications = [responses.get('q1'), responses.get('q2'), responses.get('q3')]
        
        if any(absolute_contraindications):
            return ScreeningStatus.BLOQUEADO
        
        # Q4-Q7: Contraindicações relativas
        relative_contraindications = [
            responses.get('q4'), responses.get('q5'), 
            responses.get('q6'), responses.get('q7')
        ]
        
        if any(relative_contraindications):
            return ScreeningStatus.PENDENTE_MEDICO
        
        return ScreeningStatus.APTO
    
    @staticmethod
    def can_book_ems_session(user_id, area, target_date):
        """
        Verifica se pode agendar sessão de eletrolipólise.
        Regra: Aguardar 48h entre sessões na mesma área.
        """
        # Verificar 48h na mesma área
        last_session = EMSSessionLog.query.filter_by(
            user_id=user_id,
            procedure_type=ScreeningType.ELETROLIPO,
            treatment_area=area
        ).order_by(EMSSessionLog.session_date.desc()).first()
        
        if last_session:
            hours_since = (target_date - last_session.session_date).total_seconds() / 3600
            if hours_since < 48:
                return False, f"Aguarde {int(48 - hours_since)}h para nova sessão nesta área"
        
        return True, "OK"
