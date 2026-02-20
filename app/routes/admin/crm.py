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


@crm_bp.route('/retention')
@login_required
def retention():
    """Gestao de Retencao - Health Scores e Automacoes"""
    if not _check_access():
        return "Acesso negado", 403

    from app.models.crm import StudentHealthScore, RiskLevel
    from sqlalchemy import func

    # Ultimo score de cada aluno (subquery)
    subquery = db.session.query(
        StudentHealthScore.user_id,
        func.max(StudentHealthScore.calculated_at).label('max_date')
    ).group_by(StudentHealthScore.user_id).subquery()

    recent_scores = db.session.query(StudentHealthScore).join(
        subquery,
        (StudentHealthScore.user_id == subquery.c.user_id) &
        (StudentHealthScore.calculated_at == subquery.c.max_date)
    ).all()

    # Alunos criticos e alto risco
    at_risk_students = [s for s in recent_scores
                        if s.risk_level in (RiskLevel.CRITICAL, RiskLevel.HIGH)]
    at_risk_students.sort(key=lambda s: s.total_score)

    # Stats
    total_scored = len(recent_scores)
    critical_count = sum(1 for s in recent_scores if s.risk_level == RiskLevel.CRITICAL)
    high_count = sum(1 for s in recent_scores if s.risk_level == RiskLevel.HIGH)
    avg_score = round(sum(s.total_score for s in recent_scores) / total_scored, 1) if total_scored else 0

    return render_template('admin/crm/retention.html',
                           at_risk_students=at_risk_students,
                           total_scored=total_scored,
                           critical_count=critical_count,
                           high_count=high_count,
                           avg_score=avg_score)


@crm_bp.route('/retention/calculate-scores', methods=['POST'])
@login_required
def calculate_scores():
    """Dispara calculo de Health Scores em massa"""
    if not _check_access():
        return jsonify({'error': 'Unauthorized'}), 403

    from app.services.health_score_calculator import HealthScoreCalculator
    calculator = HealthScoreCalculator()
    results = calculator.calculate_all_students()
    return jsonify({
        'success': True,
        'message': f"Processados: {results['total']}, Atualizados: {results['updated']}, "
                   f"Criticos: {results['critical']}, Alto Risco: {results['high_risk']}"
    })


@crm_bp.route('/retention/run-automations', methods=['POST'])
@login_required
def run_automations():
    """Executa automacoes diarias manualmente"""
    if not _check_access():
        return jsonify({'error': 'Unauthorized'}), 403

    from app.services.retention_automation import RetentionAutomation
    automation = RetentionAutomation()
    results = automation.run_daily_automations()
    return jsonify({
        'success': True,
        'results': results,
        'message': 'Automacoes executadas com sucesso!'
    })


@crm_bp.route('/nps')
@login_required
def nps_dashboard():
    """Dashboard de NPS - Pesquisa de satisfacao."""
    if not _check_access():
        return "Acesso negado", 403

    from app.models.crm import AutomationLog
    from sqlalchemy import func, extract

    # NPS responses are stored as automation_type = 'nps_response' or 'satisfaction_*'
    # Get all NPS-related logs
    nps_logs = AutomationLog.query.filter(
        AutomationLog.automation_type.like('nps%')
    ).order_by(AutomationLog.sent_at.desc()).all()

    # Satisfaction responses (rating-based)
    satisfaction_logs = AutomationLog.query.filter(
        AutomationLog.automation_type.like('satisfaction%')
    ).order_by(AutomationLog.sent_at.desc()).all()

    # Calculate NPS if we have data
    # Promoters (9-10), Passives (7-8), Detractors (0-6)
    promoters = 0
    passives = 0
    detractors = 0
    total_responses = len(nps_logs) + len(satisfaction_logs)

    for log in nps_logs + satisfaction_logs:
        # Try to extract rating from automation_type (e.g. 'nps_9', 'satisfaction_5')
        parts = log.automation_type.split('_')
        try:
            rating = int(parts[-1])
            if rating >= 9:
                promoters += 1
            elif rating >= 7:
                passives += 1
            else:
                detractors += 1
        except (ValueError, IndexError):
            pass

    nps_score = 0
    if total_responses > 0:
        nps_score = round(((promoters - detractors) / total_responses) * 100)

    # Monthly trend (last 6 months)
    from datetime import timedelta
    monthly_nps = []
    today = datetime.now().date()
    for i in range(5, -1, -1):
        month_date = today.replace(day=1) - timedelta(days=i * 30)
        month_start = month_date.replace(day=1)
        if month_start.month == 12:
            month_end = month_start.replace(year=month_start.year + 1, month=1, day=1)
        else:
            month_end = month_start.replace(month=month_start.month + 1, day=1)

        month_logs = [l for l in nps_logs + satisfaction_logs
                      if l.sent_at and month_start <= l.sent_at.date() < month_end]
        mp, md = 0, 0
        for l in month_logs:
            parts = l.automation_type.split('_')
            try:
                r = int(parts[-1])
                if r >= 9: mp += 1
                elif r < 7: md += 1
            except (ValueError, IndexError):
                pass

        m_total = len(month_logs)
        m_nps = round(((mp - md) / m_total) * 100) if m_total > 0 else 0
        month_names = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                       'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
        monthly_nps.append({
            'month': month_names[month_start.month - 1],
            'score': m_nps,
            'responses': m_total
        })

    # Recent detractors (to alert)
    recent_detractors = []
    for log in (nps_logs + satisfaction_logs)[:50]:
        parts = log.automation_type.split('_')
        try:
            rating = int(parts[-1])
            if rating < 7:
                recent_detractors.append({
                    'user': User.query.get(log.user_id),
                    'rating': rating,
                    'date': log.sent_at
                })
        except (ValueError, IndexError):
            pass

    return render_template('admin/crm/nps_dashboard.html',
                         nps_score=nps_score,
                         promoters=promoters,
                         passives=passives,
                         detractors=detractors,
                         total_responses=total_responses,
                         monthly_nps=monthly_nps,
                         recent_detractors=recent_detractors[:10])


@crm_bp.route('/funnel')
@login_required
def funnel():
    """Funil de conversao de visitantes."""
    if not _check_access():
        return "Acesso negado", 403

    from app.models.crm import Lead, LeadStatus
    from sqlalchemy import func

    # Funnel counts
    funnel_data = {}
    funnel_stages = [
        ('new', 'Novo Lead', '#6c757d'),
        ('contacted', 'Contatado', '#0d6efd'),
        ('visited', 'Visitou', '#ffc107'),
        ('trial', 'Aula Experimental', '#fd7e14'),
        ('proposal', 'Proposta', '#20c997'),
        ('won', 'Matriculado', '#198754'),
        ('lost', 'Perdido', '#dc3545'),
    ]

    for status_val, label, color in funnel_stages:
        try:
            count = Lead.query.filter_by(status=LeadStatus(status_val)).count()
        except ValueError:
            count = 0
        funnel_data[status_val] = {'label': label, 'count': count, 'color': color}

    total_leads = Lead.query.count()
    won_count = funnel_data.get('won', {}).get('count', 0)
    conversion_rate = round((won_count / total_leads * 100), 1) if total_leads > 0 else 0

    # Recent leads
    recent_leads = Lead.query.order_by(Lead.created_at.desc()).limit(10).all()

    return render_template('admin/crm/funnel.html',
                         funnel_data=funnel_data,
                         funnel_stages=funnel_stages,
                         total_leads=total_leads,
                         conversion_rate=conversion_rate,
                         recent_leads=recent_leads)
