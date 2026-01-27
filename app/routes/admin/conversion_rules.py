# app/routes/admin/conversion_rules.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from app.models import ConversionRule, XPConversion, User
from app.models.xp_ledger import XPLedger
from app.models.credit_wallet import CreditWallet
from app import db
from app.routes.admin.dashboard import admin_required
from datetime import datetime, timedelta
from sqlalchemy import func

conversion_rules_bp = Blueprint('admin_conversion_rules', __name__, url_prefix='/admin/conversion-rules')


@conversion_rules_bp.route('/')
@login_required
@admin_required
def list_rules():
    """Lista todas as regras de conversao"""
    rules = ConversionRule.query.order_by(ConversionRule.priority.desc(), ConversionRule.xp_required).all()

    # Estatisticas gerais
    total_conversions = XPConversion.query.count()
    total_xp_spent = db.session.query(func.coalesce(func.sum(XPConversion.xp_spent), 0)).scalar()
    total_credits_granted = db.session.query(func.coalesce(func.sum(XPConversion.credits_granted), 0)).scalar()

    # Estatisticas do mes
    start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_stats = XPConversion.get_monthly_stats()

    return render_template('admin/conversion_rules/list.html',
        rules=rules,
        total_conversions=total_conversions,
        total_xp_spent=total_xp_spent,
        total_credits_granted=total_credits_granted,
        monthly_stats=monthly_stats
    )


@conversion_rules_bp.route('/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_rule():
    """Criar nova regra de conversao"""
    if request.method == 'POST':
        # Processar cooldown_days e max_uses_per_user (podem ser vazios = None)
        cooldown_days = request.form.get('cooldown_days')
        cooldown_days = int(cooldown_days) if cooldown_days and cooldown_days.strip() else None

        max_uses = request.form.get('max_uses_per_user')
        max_uses = int(max_uses) if max_uses and max_uses.strip() else None

        rule = ConversionRule(
            name=request.form['name'],
            description=request.form.get('description'),
            xp_required=int(request.form['xp_required']),
            credits_granted=int(request.form['credits_granted']),
            credit_validity_days=int(request.form['credit_validity_days']),
            is_active=bool(request.form.get('is_active')),
            is_automatic=bool(request.form.get('is_automatic')),
            max_uses_per_user=max_uses,
            cooldown_days=cooldown_days,
            priority=int(request.form.get('priority', 0))
        )

        db.session.add(rule)
        db.session.commit()

        flash(f'Regra "{rule.name}" criada com sucesso!', 'success')
        return redirect(url_for('admin_conversion_rules.list_rules'))

    return render_template('admin/conversion_rules/form.html', rule=None)


@conversion_rules_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_rule(id):
    """Editar regra existente"""
    rule = ConversionRule.query.get_or_404(id)

    if request.method == 'POST':
        cooldown_days = request.form.get('cooldown_days')
        cooldown_days = int(cooldown_days) if cooldown_days and cooldown_days.strip() else None

        max_uses = request.form.get('max_uses_per_user')
        max_uses = int(max_uses) if max_uses and max_uses.strip() else None

        rule.name = request.form['name']
        rule.description = request.form.get('description')
        rule.xp_required = int(request.form['xp_required'])
        rule.credits_granted = int(request.form['credits_granted'])
        rule.credit_validity_days = int(request.form['credit_validity_days'])
        rule.is_active = bool(request.form.get('is_active'))
        rule.is_automatic = bool(request.form.get('is_automatic'))
        rule.max_uses_per_user = max_uses
        rule.cooldown_days = cooldown_days
        rule.priority = int(request.form.get('priority', 0))

        db.session.commit()

        flash(f'Regra "{rule.name}" atualizada!', 'success')
        return redirect(url_for('admin_conversion_rules.list_rules'))

    return render_template('admin/conversion_rules/form.html', rule=rule)


@conversion_rules_bp.route('/toggle/<int:id>', methods=['POST'])
@login_required
@admin_required
def toggle_rule(id):
    """Ativar/desativar regra"""
    rule = ConversionRule.query.get_or_404(id)
    rule.is_active = not rule.is_active
    db.session.commit()

    status = "ativada" if rule.is_active else "desativada"
    flash(f'Regra "{rule.name}" {status}.', 'info')
    return redirect(url_for('admin_conversion_rules.list_rules'))


@conversion_rules_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_rule(id):
    """Deletar regra (soft delete - apenas desativa)"""
    rule = ConversionRule.query.get_or_404(id)

    # Verifica se tem conversoes associadas
    if rule.conversions.count() > 0:
        rule.is_active = False
        db.session.commit()
        flash(f'Regra "{rule.name}" desativada (possui conversoes associadas).', 'warning')
    else:
        db.session.delete(rule)
        db.session.commit()
        flash(f'Regra "{rule.name}" removida.', 'success')

    return redirect(url_for('admin_conversion_rules.list_rules'))


@conversion_rules_bp.route('/report')
@login_required
@admin_required
def conversion_report():
    """Relatorio detalhado de conversoes"""
    # Periodo (default: ultimo mes)
    period = request.args.get('period', '30')
    days = int(period)
    start_date = datetime.utcnow() - timedelta(days=days)

    # Conversoes no periodo
    conversions = XPConversion.query.filter(
        XPConversion.converted_at >= start_date
    ).order_by(XPConversion.converted_at.desc()).all()

    # Estatisticas por regra
    rule_stats = db.session.query(
        ConversionRule.id,
        ConversionRule.name,
        func.count(XPConversion.id).label('count'),
        func.coalesce(func.sum(XPConversion.xp_spent), 0).label('xp_spent'),
        func.coalesce(func.sum(XPConversion.credits_granted), 0).label('credits_granted')
    ).outerjoin(XPConversion, db.and_(
        XPConversion.rule_id == ConversionRule.id,
        XPConversion.converted_at >= start_date
    )).group_by(ConversionRule.id).all()

    # Resumo geral
    total_conversions = len(conversions)
    total_xp = sum(c.xp_spent for c in conversions)
    total_credits = sum(c.credits_granted for c in conversions)
    unique_users = len(set(c.user_id for c in conversions))

    # Top usuarios
    top_users = db.session.query(
        User.id,
        User.name,
        func.count(XPConversion.id).label('conversion_count'),
        func.sum(XPConversion.credits_granted).label('total_credits')
    ).join(XPConversion).filter(
        XPConversion.converted_at >= start_date
    ).group_by(User.id).order_by(func.sum(XPConversion.credits_granted).desc()).limit(10).all()

    return render_template('admin/conversion_rules/report.html',
        conversions=conversions[:50],  # Limita a 50 mais recentes
        rule_stats=rule_stats,
        total_conversions=total_conversions,
        total_xp=total_xp,
        total_credits=total_credits,
        unique_users=unique_users,
        top_users=top_users,
        period=period
    )


@conversion_rules_bp.route('/api/stats')
@login_required
@admin_required
def api_stats():
    """API para estatisticas em tempo real (AJAX)"""
    # Ultimos 7 dias
    stats = []
    for i in range(7):
        date = datetime.utcnow().date() - timedelta(days=i)
        start = datetime.combine(date, datetime.min.time())
        end = datetime.combine(date, datetime.max.time())

        count = XPConversion.query.filter(
            XPConversion.converted_at >= start,
            XPConversion.converted_at <= end
        ).count()

        stats.append({
            'date': date.strftime('%d/%m'),
            'count': count
        })

    return jsonify(list(reversed(stats)))
