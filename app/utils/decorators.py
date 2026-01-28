from functools import wraps
from flask import redirect, url_for, flash, request
from flask_login import current_user
from app.models.health import ScreeningType, ScreeningStatus

def requires_health_screening(screening_type=ScreeningType.PARQ):
    """
    Decorator que exige que o usuário tenha uma triagem de saúde válida e aprovada.
    Se não tiver, redireciona para o formulário.
    Se estiver pendente médico, redireciona para a tela de aviso.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return f(*args, **kwargs)
            
            # Verificar status
            status = current_user.get_screening_status(screening_type)
            
            if status is None:
                # Nunca preencheu
                if screening_type == ScreeningType.PARQ:
                    flash('Para sua segurança, por favor preencha o questionário de saúde antes de prosseguir. 😊', 'info')
                    return redirect(url_for('health.fill_parq', next=request.url))
                # Adicionar outros tipos conforme necessário (EMS, etc)
                
            elif status == ScreeningStatus.EXPIRADO:
                flash('Seu questionário de saúde expirou. Por favor, renove-o para continuar. ⏰', 'warning')
                if screening_type == ScreeningType.PARQ:
                    return redirect(url_for('health.fill_parq', next=request.url))
                
            elif status == ScreeningStatus.PENDENTE_MEDICO:
                # Verificamos se ele já enviou o atestado
                from app.models.health import HealthScreening
                screening = HealthScreening.query.filter_by(
                    user_id=current_user.id,
                    screening_type=screening_type,
                    status=ScreeningStatus.PENDENTE_MEDICO
                ).order_by(HealthScreening.created_at.desc()).first()
                
                if screening and screening.medical_certificate_url:
                    # Já enviou, está aguardando admin
                    flash('Sua triagem de saúde está aguardando revisão médica. Avisaremos assim que for aprovada! 🩺', 'info')
                    return redirect(url_for('student.dashboard'))
                else:
                    # Precisa enviar atestado
                    return redirect(url_for('health.parq_pending'))
                    
            elif status == ScreeningStatus.BLOQUEADO:
                flash('Você possui contraindicações absolutas para esta atividade. Entre em contato com nosso atendimento.', 'danger')
                return redirect(url_for('student.dashboard'))
                
            # Se for APTO, segue o jogo
            return f(*args, **kwargs)
        return decorated_function
    return decorator
