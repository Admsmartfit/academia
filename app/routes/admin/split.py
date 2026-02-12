# app/routes/admin/split.py
"""
Rotas administrativas para gestao do Split Bancario Dinamico.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from decimal import Decimal

from app import db
from app.routes.admin.dashboard import admin_required
from app.models.user import User, ProfessionalType
from app.models.class_schedule import ClassSchedule
from app.models.commission import (
    CommissionEntry, CommissionStatus,
    SplitConfiguration, SplitSettings,
    PayoutBatch, PayoutStatus,
    DemandLevel, CollaboratorBankInfo
)
from app.services.split_service import split_service
from app.services.dynamic_split_algorithm import dynamic_split

split_bp = Blueprint('admin_split', __name__, url_prefix='/admin/split')


# =============================================================================
# Dashboard Principal
# =============================================================================

@split_bp.route('/')
@login_required
@admin_required
def dashboard():
    """Dashboard do modulo de Split Bancario."""
    settings = SplitSettings.get_settings()

    # Estatisticas gerais
    pending_suggestions = SplitConfiguration.query.filter_by(
        suggestion_pending=True
    ).count()

    pending_commissions = CommissionEntry.query.filter_by(
        status=CommissionStatus.PENDING
    ).count()

    pending_payouts = PayoutBatch.query.filter_by(
        status=PayoutStatus.PENDING
    ).count()

    # Colaboradores ativos
    collaborators = User.query.filter(
        User.role == 'instructor',
        User.is_active == True
    ).count()

    # Totais do mes atual
    now = datetime.now()
    month_start = datetime(now.year, now.month, 1)

    month_commissions = db.session.query(
        db.func.sum(CommissionEntry.amount_professional)
    ).filter(
        CommissionEntry.processed_at >= month_start
    ).scalar() or 0

    month_academy = db.session.query(
        db.func.sum(CommissionEntry.amount_academy)
    ).filter(
        CommissionEntry.processed_at >= month_start
    ).scalar() or 0

    return render_template('admin/split/dashboard.html',
        settings=settings,
        pending_suggestions=pending_suggestions,
        pending_commissions=pending_commissions,
        pending_payouts=pending_payouts,
        collaborators=collaborators,
        month_commissions=month_commissions,
        month_academy=month_academy,
        current_month=now.strftime('%B %Y')
    )


# =============================================================================
# Configuracoes Globais
# =============================================================================

@split_bp.route('/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def settings():
    """Configuracoes globais do sistema de split."""
    settings = SplitSettings.get_settings()

    if request.method == 'POST':
        try:
            settings.credit_value_reais = Decimal(request.form.get('credit_value_reais', '15.00'))

            settings.low_demand_academy_pct = Decimal(request.form.get('low_demand_academy_pct', '20.00'))
            settings.low_demand_professional_pct = Decimal('100.00') - settings.low_demand_academy_pct

            settings.standard_demand_academy_pct = Decimal(request.form.get('standard_demand_academy_pct', '40.00'))
            settings.standard_demand_professional_pct = Decimal('100.00') - settings.standard_demand_academy_pct

            settings.high_demand_academy_pct = Decimal(request.form.get('high_demand_academy_pct', '60.00'))
            settings.high_demand_professional_pct = Decimal('100.00') - settings.high_demand_academy_pct

            settings.low_demand_threshold = Decimal(request.form.get('low_demand_threshold', '40.00'))
            settings.high_demand_threshold = Decimal(request.form.get('high_demand_threshold', '80.00'))

            settings.suggestion_job_enabled = bool(request.form.get('suggestion_job_enabled'))
            settings.suggestion_lookback_days = int(request.form.get('suggestion_lookback_days', '30'))

            settings.updated_by_id = current_user.id
            db.session.commit()

            flash('Configuracoes atualizadas com sucesso!', 'success')
        except Exception as e:
            flash(f'Erro ao atualizar: {e}', 'danger')

        return redirect(url_for('admin_split.settings'))

    return render_template('admin/split/settings.html', settings=settings)


# =============================================================================
# Sugestoes de Split (Algoritmo Dinamico)
# =============================================================================

@split_bp.route('/suggestions')
@login_required
@admin_required
def suggestions():
    """Lista sugestoes de ajuste de split pendentes."""
    suggestions = dynamic_split.get_pending_suggestions()

    return render_template('admin/split/suggestions.html',
        suggestions=suggestions
    )


@split_bp.route('/suggestions/generate', methods=['POST'])
@login_required
@admin_required
def generate_suggestions():
    """Executa o algoritmo para gerar novas sugestoes."""
    stats = dynamic_split.generate_suggestions()

    if stats.get('status') == 'disabled':
        flash('Job de sugestao esta desabilitado nas configuracoes.', 'warning')
    else:
        flash(
            f"Analise concluida: {stats['suggestions_created']} sugestoes criadas, "
            f"{stats['no_change_needed']} sem alteracao necessaria.",
            'success'
        )

    return redirect(url_for('admin_split.suggestions'))


@split_bp.route('/suggestions/<int:config_id>/apply', methods=['POST'])
@login_required
@admin_required
def apply_suggestion(config_id):
    """Aplica uma sugestao de split."""
    if dynamic_split.apply_suggestion(config_id, current_user):
        flash('Sugestao aplicada com sucesso!', 'success')
    else:
        flash('Erro ao aplicar sugestao.', 'danger')

    return redirect(url_for('admin_split.suggestions'))


@split_bp.route('/suggestions/<int:config_id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_suggestion(config_id):
    """Rejeita uma sugestao de split."""
    if dynamic_split.reject_suggestion(config_id, current_user):
        flash('Sugestao rejeitada.', 'info')
    else:
        flash('Erro ao rejeitar sugestao.', 'danger')

    return redirect(url_for('admin_split.suggestions'))


@split_bp.route('/suggestions/apply-all', methods=['POST'])
@login_required
@admin_required
def apply_all_suggestions():
    """Aplica todas as sugestoes pendentes."""
    count = dynamic_split.apply_all_suggestions(current_user)
    flash(f'{count} sugestoes aplicadas com sucesso!', 'success')
    return redirect(url_for('admin_split.suggestions'))


# =============================================================================
# Configuracao de Split por Horario
# =============================================================================

@split_bp.route('/schedules')
@login_required
@admin_required
def schedules():
    """Lista horarios com configuracao de split."""
    schedules = ClassSchedule.query.filter_by(is_active=True).order_by(
        ClassSchedule.weekday,
        ClassSchedule.start_time
    ).all()

    # Adicionar analise de cada horario
    schedule_data = []
    for schedule in schedules:
        config = schedule.split_config
        schedule_data.append({
            'schedule': schedule,
            'config': config,
            'occupancy': float(schedule.avg_occupancy_rate or 0),
            'split_rate': float(schedule.current_split_rate or 60)
        })

    return render_template('admin/split/schedules.html',
        schedules=schedule_data
    )


@split_bp.route('/schedules/<int:schedule_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_schedule_split(schedule_id):
    """Edita split de um horario especifico."""
    schedule = ClassSchedule.query.get_or_404(schedule_id)

    if request.method == 'POST':
        academy_pct = Decimal(request.form.get('academy_pct', '40'))
        professional_pct = Decimal('100.00') - academy_pct

        try:
            dynamic_split.set_manual_split(
                schedule_id,
                academy_pct,
                professional_pct,
                current_user
            )
            flash('Split atualizado com sucesso!', 'success')
        except ValueError as e:
            flash(f'Erro: {e}', 'danger')

        return redirect(url_for('admin_split.schedules'))

    analysis = dynamic_split.analyze_schedule(schedule)

    return render_template('admin/split/edit_schedule.html',
        schedule=schedule,
        analysis=analysis
    )


# =============================================================================
# Comissoes
# =============================================================================

@split_bp.route('/commissions')
@login_required
@admin_required
def commissions():
    """Lista de comissoes."""
    status = request.args.get('status')
    professional_id = request.args.get('professional_id', type=int)

    query = CommissionEntry.query

    if status:
        query = query.filter_by(status=CommissionStatus(status))
    if professional_id:
        query = query.filter_by(professional_id=professional_id)

    commissions = query.order_by(CommissionEntry.processed_at.desc()).limit(100).all()

    # Lista de colaboradores para filtro
    professionals = User.query.filter(
        User.role == 'instructor'
    ).order_by(User.name).all()

    return render_template('admin/split/commissions.html',
        commissions=commissions,
        professionals=professionals,
        current_status=status,
        current_professional=professional_id
    )


@split_bp.route('/commissions/process', methods=['POST'])
@login_required
@admin_required
def process_commissions():
    """Processa comissoes pendentes de bookings finalizados."""
    stats = split_service.process_pending_bookings()

    flash(
        f"Processamento concluido: {stats['processed']} comissoes criadas, "
        f"{stats['skipped']} ignoradas, {stats['errors']} erros.",
        'success' if stats['errors'] == 0 else 'warning'
    )

    return redirect(url_for('admin_split.commissions'))


# =============================================================================
# Payouts (Pagamentos)
# =============================================================================

@split_bp.route('/payouts')
@login_required
@admin_required
def payouts():
    """Lista de lotes de pagamento."""
    status = request.args.get('status')

    query = PayoutBatch.query

    if status:
        query = query.filter_by(status=PayoutStatus(status))

    payouts = query.order_by(
        PayoutBatch.reference_year.desc(),
        PayoutBatch.reference_month.desc()
    ).all()

    return render_template('admin/split/payouts.html',
        payouts=payouts,
        current_status=status
    )


@split_bp.route('/payouts/generate', methods=['GET', 'POST'])
@login_required
@admin_required
def generate_payouts():
    """Gera lotes de pagamento para um mes."""
    if request.method == 'POST':
        month = int(request.form.get('month'))
        year = int(request.form.get('year'))

        batches = split_service.generate_monthly_payouts(month, year)

        flash(f'{len(batches)} lotes de pagamento gerados para {month}/{year}!', 'success')
        return redirect(url_for('admin_split.payouts'))

    now = datetime.now()
    return render_template('admin/split/generate_payouts.html',
        current_month=now.month,
        current_year=now.year
    )


@split_bp.route('/payouts/<int:batch_id>')
@login_required
@admin_required
def payout_detail(batch_id):
    """Detalhes de um lote de pagamento."""
    batch = PayoutBatch.query.get_or_404(batch_id)

    return render_template('admin/split/payout_detail.html',
        batch=batch
    )


@split_bp.route('/payouts/<int:batch_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_payout(batch_id):
    """Aprova um lote de pagamento."""
    batch = PayoutBatch.query.get_or_404(batch_id)

    try:
        batch.approve(current_user)
        db.session.commit()
        flash('Lote aprovado com sucesso!', 'success')
    except ValueError as e:
        flash(f'Erro: {e}', 'danger')

    return redirect(url_for('admin_split.payout_detail', batch_id=batch_id))


@split_bp.route('/payouts/<int:batch_id>/mark-paid', methods=['POST'])
@login_required
@admin_required
def mark_payout_paid(batch_id):
    """Marca lote como pago."""
    batch = PayoutBatch.query.get_or_404(batch_id)

    payment_ref = request.form.get('payment_reference')
    proof_url = request.form.get('proof_url')

    try:
        batch.mark_as_paid(payment_ref, proof_url)
        db.session.commit()
        flash('Lote marcado como pago!', 'success')
    except ValueError as e:
        flash(f'Erro: {e}', 'danger')

    return redirect(url_for('admin_split.payout_detail', batch_id=batch_id))


# =============================================================================
# Colaboradores
# =============================================================================

@split_bp.route('/collaborators')
@login_required
@admin_required
def collaborators():
    """Lista colaboradores com informacoes de comissao."""
    collaborators = User.query.filter(
        User.role == 'instructor',
        User.is_active == True
    ).order_by(User.name).all()

    # Adicionar estatisticas de cada colaborador
    collab_data = []
    for collab in collaborators:
        pending = db.session.query(
            db.func.sum(CommissionEntry.amount_professional)
        ).filter(
            CommissionEntry.professional_id == collab.id,
            CommissionEntry.status == CommissionStatus.PENDING
        ).scalar() or 0

        total_paid = db.session.query(
            db.func.sum(CommissionEntry.amount_professional)
        ).filter(
            CommissionEntry.professional_id == collab.id,
            CommissionEntry.status == CommissionStatus.PAID
        ).scalar() or 0

        collab_data.append({
            'user': collab,
            'pending': pending,
            'total_paid': total_paid,
            'has_bank_info': collab.bank_info is not None and collab.bank_info.can_receive_payment
        })

    return render_template('admin/split/collaborators.html',
        collaborators=collab_data
    )


@split_bp.route('/collaborators/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_collaborator(user_id):
    """Edita dados de comissao de um colaborador."""
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        user.professional_type = ProfessionalType(request.form.get('professional_type', 'instructor'))

        base_rate = request.form.get('base_commission_rate')
        if base_rate:
            user.base_commission_rate = Decimal(base_rate)
        else:
            user.base_commission_rate = None

        db.session.commit()
        flash('Dados atualizados!', 'success')
        return redirect(url_for('admin_split.collaborators'))

    return render_template('admin/split/edit_collaborator.html',
        user=user,
        professional_types=ProfessionalType
    )


@split_bp.route('/collaborators/<int:user_id>/statement')
@login_required
@admin_required
def collaborator_statement(user_id):
    """Extrato de comissoes de um colaborador."""
    month = request.args.get('month', type=int)
    year = request.args.get('year', type=int)

    statement = split_service.get_collaborator_statement(user_id, month, year)

    return render_template('admin/split/statement.html',
        statement=statement
    )


@split_bp.route('/collaborators/<int:user_id>/statement/pdf')
@login_required
@admin_required
def export_statement_pdf(user_id):
    """Exporta extrato em PDF."""
    from flask import Response
    from app.services.pdf_generator import pdf_generator

    month = request.args.get('month', type=int)
    year = request.args.get('year', type=int)

    statement = split_service.get_collaborator_statement(user_id, month, year)
    pdf_bytes = pdf_generator.generate_statement_pdf(statement)

    prof_name = statement['professional']['name'].replace(' ', '_')
    m = statement['period']['month']
    y = statement['period']['year']
    filename = f"extrato_{prof_name}_{m:02d}_{y}.pdf"

    return Response(
        pdf_bytes,
        mimetype='application/pdf',
        headers={
            'Content-Disposition': f'attachment; filename="{filename}"'
        }
    )


# =============================================================================
# API Endpoints
# =============================================================================

@split_bp.route('/api/stats')
@login_required
@admin_required
def api_stats():
    """API: Estatisticas do sistema de split."""
    settings = SplitSettings.get_settings()
    now = datetime.now()
    month_start = datetime(now.year, now.month, 1)

    stats = {
        'credit_value': float(settings.credit_value_reais),
        'pending_suggestions': SplitConfiguration.query.filter_by(suggestion_pending=True).count(),
        'pending_commissions': CommissionEntry.query.filter_by(status=CommissionStatus.PENDING).count(),
        'pending_payouts': PayoutBatch.query.filter_by(status=PayoutStatus.PENDING).count(),
        'month_total_professional': float(
            db.session.query(db.func.sum(CommissionEntry.amount_professional))
            .filter(CommissionEntry.processed_at >= month_start).scalar() or 0
        ),
        'month_total_academy': float(
            db.session.query(db.func.sum(CommissionEntry.amount_academy))
            .filter(CommissionEntry.processed_at >= month_start).scalar() or 0
        )
    }

    return jsonify(stats)
