from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models.health import HealthScreening, ScreeningStatus, ScreeningType
from app.models.user import User
from app import db
from app.routes.admin.dashboard import admin_required
from datetime import datetime

admin_health_bp = Blueprint('admin_health', __name__, url_prefix='/admin/health')

@admin_health_bp.route('/pending')
@login_required
@admin_required
def pending_screenings():
    """Lista de triagens pendentes de aprovação médica"""
    pending = HealthScreening.query.filter(
        HealthScreening.status == ScreeningStatus.PENDENTE_MEDICO,
        HealthScreening.medical_certificate_url != None
    ).order_by(HealthScreening.medical_certificate_uploaded_at.asc()).all()
    
    return render_template('admin/health/pending.html', screenings=pending)

@admin_health_bp.route('/approve/<int:id>', methods=['POST'])
@login_required
@admin_required
def approve_screening(id):
    """Aprova uma triagem médica"""
    screening = HealthScreening.query.get_or_404(id)
    notes = request.form.get('notes')
    
    screening.status = ScreeningStatus.APTO
    screening.approved_by_id = current_user.id
    screening.approved_at = datetime.utcnow()
    screening.approval_notes = notes
    
    db.session.commit()
    
    flash(f'Triagem de {screening.user.name} aprovada com sucesso!', 'success')
    return redirect(url_for('admin_health.pending_screenings'))

@admin_health_bp.route('/reject/<int:id>', methods=['POST'])
@login_required
@admin_required
def reject_screening(id):
    """Rejeita uma triagem médica (ex: atestado inválido)"""
    screening = HealthScreening.query.get_or_404(id)
    notes = request.form.get('notes')
    
    if not notes:
        flash('Por favor, informe o motivo da rejeição.', 'warning')
        return redirect(url_for('admin_health.pending_screenings'))
    
    # Mantém como pendente mas limpa o atestado para novo upload
    # OU podemos criar um novo status REJEITADO?
    # O PRD diz "Notificações ao aprovar/reprovar".
    # Vou manter como PENDENTE_MEDICO mas registrar a nota
    
    screening.approval_notes = notes
    screening.medical_certificate_url = None # Forçar novo upload
    
    db.session.commit()
    
    flash(f'Triagem de {screening.user.name} rejeitada. O aluno deverá enviar novo documento.', 'info')
    return redirect(url_for('admin_health.pending_screenings'))
