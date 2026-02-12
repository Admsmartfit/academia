from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
from app import db
from app.models.crm import Lead, LeadSource, LeadStatus
from app.models.user import User

crm_bp = Blueprint('crm', __name__, url_prefix='/admin/crm')


def _check_access():
    return current_user.is_admin or current_user.role == 'manager'


@crm_bp.route('/dashboard')
@login_required
def dashboard():
    """Dashboard de CRM e Retencao"""
    if not _check_access():
        return "Acesso negado", 403
    return render_template('admin/crm/dashboard.html')


@crm_bp.route('/leads')
@login_required
def leads():
    """Pipeline de Leads"""
    if not _check_access():
        return "Acesso negado", 403

    leads_by_status = {}
    for status in LeadStatus:
        leads_by_status[status.value] = Lead.query.filter_by(
            status=status
        ).order_by(Lead.created_at.desc()).all()

    sources = [{'value': s.value, 'label': s.value.replace('_', ' ').title()} for s in LeadSource]
    statuses = [{'value': s.value, 'label': Lead.query.first() and s.value or s.value} for s in LeadStatus]

    # Staff for assignment
    staff = User.query.filter(User.role.in_(['admin', 'manager', 'instructor'])).all()

    # Stats
    total = Lead.query.count()
    new_count = Lead.query.filter_by(status=LeadStatus.NEW).count()
    won_count = Lead.query.filter_by(status=LeadStatus.WON).count()
    lost_count = Lead.query.filter_by(status=LeadStatus.LOST).count()
    conversion_rate = round((won_count / total * 100), 1) if total > 0 else 0

    return render_template('admin/crm/leads.html',
                           leads_by_status=leads_by_status,
                           sources=sources,
                           staff=staff,
                           total=total,
                           new_count=new_count,
                           won_count=won_count,
                           lost_count=lost_count,
                           conversion_rate=conversion_rate)


@crm_bp.route('/leads/create', methods=['POST'])
@login_required
def create_lead():
    """Criar novo lead"""
    if not _check_access():
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.form
    lead = Lead(
        full_name=data.get('full_name'),
        email=data.get('email') or None,
        phone=data.get('phone'),
        source=LeadSource(data.get('source', 'walk_in')),
        interest_goal=data.get('interest_goal'),
        preferred_schedule=data.get('preferred_schedule'),
        budget_range=data.get('budget_range'),
        notes=data.get('notes'),
        assigned_to_id=int(data.get('assigned_to_id')) if data.get('assigned_to_id') else None
    )
    db.session.add(lead)
    db.session.commit()
    flash('Lead criado com sucesso!', 'success')
    return redirect(url_for('crm.leads'))


@crm_bp.route('/leads/<int:lead_id>/update-status', methods=['POST'])
@login_required
def update_lead_status(lead_id):
    """Atualizar status do lead (pipeline drag)"""
    if not _check_access():
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.json
    lead = Lead.query.get_or_404(lead_id)
    new_status = data.get('status')

    try:
        lead.status = LeadStatus(new_status)
        lead.last_contact_at = datetime.utcnow()

        if new_status == 'won':
            lead.converted_at = datetime.utcnow()
        elif new_status == 'lost':
            lead.lost_reason = data.get('reason', '')

        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400


@crm_bp.route('/leads/<int:lead_id>/edit', methods=['POST'])
@login_required
def edit_lead(lead_id):
    """Editar lead"""
    if not _check_access():
        return jsonify({'error': 'Unauthorized'}), 403

    lead = Lead.query.get_or_404(lead_id)
    data = request.form

    lead.full_name = data.get('full_name', lead.full_name)
    lead.email = data.get('email') or lead.email
    lead.phone = data.get('phone', lead.phone)
    lead.interest_goal = data.get('interest_goal', lead.interest_goal)
    lead.preferred_schedule = data.get('preferred_schedule', lead.preferred_schedule)
    lead.budget_range = data.get('budget_range', lead.budget_range)
    lead.notes = data.get('notes', lead.notes)
    if data.get('assigned_to_id'):
        lead.assigned_to_id = int(data.get('assigned_to_id'))
    if data.get('source'):
        lead.source = LeadSource(data.get('source'))

    db.session.commit()
    flash('Lead atualizado!', 'success')
    return redirect(url_for('crm.leads'))


@crm_bp.route('/leads/<int:lead_id>/delete', methods=['POST'])
@login_required
def delete_lead(lead_id):
    """Remover lead"""
    if not _check_access():
        return jsonify({'error': 'Unauthorized'}), 403

    lead = Lead.query.get_or_404(lead_id)
    db.session.delete(lead)
    db.session.commit()
    flash('Lead removido.', 'info')
    return redirect(url_for('crm.leads'))


@crm_bp.route('/health-overview')
@login_required
def health_overview():
    """Visao geral da Saude da Academia (Health Score)"""
    if not _check_access():
        return "Acesso negado", 403
        
    from app.models.crm import StudentHealthScore, RiskLevel
    from sqlalchemy import func
    
    # Counts by risk
    risk_counts = db.session.query(
        StudentHealthScore.risk_level, 
        func.count(StudentHealthScore.id)
    ).group_by(StudentHealthScore.risk_level).all()
    
    # Convert to dict
    stats = {r.value: 0 for r in RiskLevel}
    for r, count in risk_counts:
        stats[r.value] = count
        
    # Lists of at-risk students
    critical_students = StudentHealthScore.query.filter(
        StudentHealthScore.risk_level.in_([RiskLevel.CRITICAL, RiskLevel.HIGH])
    ).order_by(StudentHealthScore.total_score.asc()).limit(50).all()
    
    total_students = StudentHealthScore.query.count()
    
    return render_template('admin/crm/health_overview.html', 
                          stats=stats, 
                          critical_students=critical_students,
                          total_students=total_students)
