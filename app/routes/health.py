from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models.health import HealthScreening, ScreeningType, ScreeningStatus
from app.services.screening_service import ScreeningService
from app.services.health_handler import HealthHandler
from app import db
from datetime import datetime, timedelta

health_bp = Blueprint('health', __name__, url_prefix='/health')

@health_bp.route('/parq/fill', methods=['GET'])
@login_required
def fill_parq():
    """Exibe o formulário PAR-Q"""
    # Verificar se já tem um screening ativo
    if current_user.has_valid_screening(ScreeningType.PARQ):
        flash('Você já possui um questionário de saúde válido.', 'info')
        # Se tiver next, redireciona, senão dash
        next_url = request.args.get('next')
        if next_url:
            return redirect(next_url)
        return redirect(url_for('student.dashboard'))
    
    next_url = request.args.get('next')
    return render_template('health/parq_form.html', next_url=next_url)

@health_bp.route('/parq/fill', methods=['POST'])
@login_required
def submit_parq():
    """Processa o envio do formulário PAR-Q"""
    responses = {}
    for i in range(1, 8):
        val = request.form.get(f'q{i}')
        if val is None:
            flash('Por favor, responda todas as perguntas.', 'warning')
            return redirect(url_for('health.fill_parq', next=request.form.get('next')))
        responses[f'q{i}'] = val == 'sim'

    # Validar respostas
    status = ScreeningService.validate_parq_responses(responses)
    
    # Calcular validade (12 meses)
    expires_at = datetime.utcnow() + timedelta(days=365)
    
    # Criar registro
    screening = HealthScreening(
        user_id=current_user.id,
        screening_type=ScreeningType.PARQ,
        responses=responses,
        status=status,
        acceptance_ip=request.remote_addr,
        expires_at=expires_at,
        accepted_terms=True
    )
    
    db.session.add(screening)
    db.session.commit()
    
    if status == ScreeningStatus.APTO:
        next_url = request.form.get('next')
        if next_url:
            flash('Questionário de saúde aprovado! Vamos continuar. 🚀', 'success')
            return redirect(next_url)
        return redirect(url_for('health.parq_success'))
    else:
        return redirect(url_for('health.parq_pending'))

@health_bp.route('/upload-certificate', methods=['POST'])
@login_required
def upload_certificate():
    """Processa o upload de atestado médico"""
    if 'certificate' not in request.files:
        flash('Nenhum arquivo enviado.', 'danger')
        return redirect(url_for('health.parq_pending'))
    
    file = request.files['certificate']
    if file.filename == '':
        flash('Nenhum arquivo selecionado.', 'danger')
        return redirect(url_for('health.parq_pending'))
    
    try:
        # Buscar o screening mais recente pendente
        screening = HealthScreening.query.filter_by(
            user_id=current_user.id,
            status=ScreeningStatus.PENDENTE_MEDICO
        ).order_by(HealthScreening.created_at.desc()).first()
        
        if not screening:
            flash('Não encontramos uma solicitação de atestado pendente.', 'warning')
            return redirect(url_for('student.dashboard'))

        url = HealthHandler.save_certificate(file, current_user.id)
        
        screening.medical_certificate_url = url
        screening.medical_certificate_uploaded_at = datetime.utcnow()
        db.session.commit()
        
        flash('Atestado enviado com sucesso! Nossa equipe irá revisar em breve. 😊', 'success')
        return redirect(url_for('student.dashboard'))
        
    except ValueError as e:
        flash(str(e), 'danger')
        return redirect(url_for('health.parq_pending'))
    except Exception as e:
        flash(f'Erro ao salvar arquivo: {str(e)}', 'danger')
        return redirect(url_for('health.parq_pending'))

@health_bp.route('/parq/terms', methods=['GET'])
@login_required
def parq_terms():
    """Exibe o termo de consentimento"""
    return render_template('health/parq_terms.html')

@health_bp.route('/parq/success')
@login_required
def parq_success():
    """Tela de sucesso para quem está APTO"""
    return render_template('health/success.html', status='apto')

@health_bp.route('/parq/pending')
@login_required
def parq_pending():
    """Tela informativa para quem está PENDENTE_MEDICO"""
    return render_template('health/success.html', status='pendente')

@health_bp.route('/ems/fill', methods=['GET'])
@login_required
def fill_ems():
    """Exibe o formulário de anamnese EMS"""
    if current_user.has_valid_screening(ScreeningType.EMS):
        flash('Você já possui uma anamnese EMS válida.', 'info')
        return redirect(url_for('student.dashboard'))
    
    return render_template('health/ems_form.html')

@health_bp.route('/ems/fill', methods=['POST'])
@login_required
def submit_ems():
    """Processa o envio da anamnese EMS"""
    responses = {}
    for i in range(1, 11): # Q1 a Q10
        val = request.form.get(f'q{i}')
        if val is None:
            flash('Por favor, responda todas as perguntas.', 'warning')
            return redirect(url_for('health.fill_ems'))
        responses[f'q{i}'] = val == 'sim'

    # Validar respostas
    status = ScreeningService.validate_ems_responses(responses)
    
    # Validade: 6 meses para EMS
    expires_at = datetime.utcnow() + timedelta(days=180)
    
    screening = HealthScreening(
        user_id=current_user.id,
        screening_type=ScreeningType.EMS,
        responses=responses,
        status=status,
        acceptance_ip=request.remote_addr,
        expires_at=expires_at,
        accepted_terms=True
    )
    
    db.session.add(screening)
    db.session.commit()
    
    if status == ScreeningStatus.APTO:
        flash('Anamnese EMS concluída com sucesso! Você está apto. 🚀', 'success')
        return redirect(url_for('student.dashboard'))
    elif status == ScreeningStatus.BLOQUEADO:
        return redirect(url_for('health.ems_blocked'))
    else:
        flash('Recebemos sua anamnese. Como você respondeu SIM para algumas questões, precisamos de um atestado médico. 🩺', 'info')
        return redirect(url_for('health.parq_pending'))

@health_bp.route('/ems/blocked')
@login_required
def ems_blocked():
    """Tela de bloqueio total para EMS"""
    return render_template('health/ems_blocked.html')


