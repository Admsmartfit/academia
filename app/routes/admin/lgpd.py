# app/routes/admin/lgpd.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.routes.admin.dashboard import admin_required
from datetime import datetime, timedelta

lgpd_bp = Blueprint('admin_lgpd', __name__, url_prefix='/admin/lgpd')


@lgpd_bp.route('/')
@login_required
@admin_required
def index():
    """Painel LGPD e Seguranca."""
    from app.models.consent_log import ConsentLog, ConsentType
    from app.models.audit_log import AuditLog, AuditAction

    # Stats de consentimento
    total_consents = ConsentLog.query.filter_by(accepted=True, revoked_at=None).count()
    revoked_consents = ConsentLog.query.filter(ConsentLog.revoked_at.isnot(None)).count()

    # Consentimentos por tipo
    consent_stats = {}
    for ct in ConsentType:
        active = ConsentLog.query.filter_by(consent_type=ct, accepted=True, revoked_at=None).count()
        consent_stats[ct.value] = {'label': ct.label, 'count': active}

    # Ultimos logs de auditoria
    recent_logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(20).all()

    # Stats de auditoria
    today = datetime.now().date()
    logs_today = AuditLog.query.filter(
        AuditLog.created_at >= datetime.combine(today, datetime.min.time())
    ).count()

    failed_logins = AuditLog.query.filter(
        AuditLog.action == AuditAction.LOGIN_FAILED,
        AuditLog.created_at >= datetime.combine(today, datetime.min.time())
    ).count()

    return render_template('admin/lgpd/index.html',
                           total_consents=total_consents,
                           revoked_consents=revoked_consents,
                           consent_stats=consent_stats,
                           recent_logs=recent_logs,
                           logs_today=logs_today,
                           failed_logins=failed_logins)


@lgpd_bp.route('/audit-logs')
@login_required
@admin_required
def audit_logs():
    """Logs de auditoria detalhados."""
    from app.models.audit_log import AuditLog, AuditAction

    page = request.args.get('page', 1, type=int)
    action_filter = request.args.get('action', '')
    user_filter = request.args.get('user_id', '', type=str)

    query = AuditLog.query

    if action_filter:
        try:
            query = query.filter(AuditLog.action == AuditAction(action_filter))
        except ValueError:
            pass

    if user_filter:
        try:
            query = query.filter(AuditLog.user_id == int(user_filter))
        except ValueError:
            pass

    logs = query.order_by(AuditLog.created_at.desc()).paginate(
        page=page, per_page=50, error_out=False
    )

    actions = [{'value': a.value, 'label': a.label} for a in AuditAction]

    return render_template('admin/lgpd/audit_logs.html',
                           logs=logs,
                           actions=actions,
                           action_filter=action_filter,
                           user_filter=user_filter)


@lgpd_bp.route('/user/<int:user_id>/consents')
@login_required
@admin_required
def user_consents(user_id):
    """Ver consentimentos de um usuario."""
    from app.models.user import User
    from app.models.consent_log import ConsentLog

    user = User.query.get_or_404(user_id)
    consents = ConsentLog.query.filter_by(user_id=user_id).order_by(ConsentLog.created_at.desc()).all()

    return render_template('admin/lgpd/user_consents.html',
                           user=user,
                           consents=consents)


@lgpd_bp.route('/user/<int:user_id>/anonymize', methods=['POST'])
@login_required
@admin_required
def anonymize_user(user_id):
    """Anonimizar dados do usuario (Direito ao Esquecimento)."""
    from app.models.user import User
    from app.models.audit_log import AuditLog, AuditAction
    from app.models.consent_log import ConsentLog
    import hashlib

    user = User.query.get_or_404(user_id)

    if user.role == 'admin':
        flash('Nao e possivel anonimizar contas de administrador.', 'danger')
        return redirect(url_for('admin_users.list_users'))

    # Salvar dados originais para log
    old_data = f"nome={user.name}, email={user.email}, phone={user.phone}"

    # Anonimizar - manter ID para referencia financeira
    anon_hash = hashlib.md5(str(user.id).encode()).hexdigest()[:8]
    user.name = f"Usuario Anonimizado #{anon_hash}"
    user.email = f"anon_{anon_hash}@removed.lgpd"
    user.phone = None
    user.cpf = None
    user.is_active = False

    # Revogar todos os consentimentos
    active_consents = ConsentLog.query.filter_by(user_id=user_id, accepted=True, revoked_at=None).all()
    for consent in active_consents:
        consent.revoke()

    # Registrar auditoria
    AuditLog.log(
        action=AuditAction.DATA_ANONYMIZE,
        user_id=current_user.id,
        entity_type='User',
        entity_id=user_id,
        description=f'Dados anonimizados por {current_user.name}',
        old_value=old_data,
        new_value=f'nome=Usuario Anonimizado #{anon_hash}',
        ip_address=request.remote_addr
    )

    db.session.commit()
    flash(f'Dados do usuario #{user_id} foram anonimizados conforme LGPD.', 'info')
    return redirect(url_for('admin_users.list_users'))


@lgpd_bp.route('/user/<int:user_id>/export')
@login_required
@admin_required
def export_user_data(user_id):
    """Exportar dados do usuario (Portabilidade LGPD)."""
    from app.models.user import User
    from app.models.audit_log import AuditLog, AuditAction
    import json

    user = User.query.get_or_404(user_id)

    # Compilar todos os dados do usuario
    data = {
        'dados_pessoais': {
            'nome': user.name,
            'email': user.email,
            'telefone': user.phone,
            'cpf': user.cpf if hasattr(user, 'cpf') else None,
            'data_cadastro': user.created_at.isoformat() if user.created_at else None,
        },
        'assinaturas': [],
        'pagamentos': [],
        'agendamentos': [],
        'consentimentos': [],
    }

    # Assinaturas
    for sub in user.subscriptions if hasattr(user, 'subscriptions') else []:
        data['assinaturas'].append({
            'pacote': sub.package.name if sub.package else '-',
            'status': sub.status.value,
            'inicio': sub.start_date.isoformat() if sub.start_date else None,
            'fim': sub.end_date.isoformat() if sub.end_date else None,
        })
        # Pagamentos
        for p in sub.payments:
            data['pagamentos'].append({
                'parcela': f'{p.installment_number}/{p.installment_total}',
                'valor': float(p.amount),
                'vencimento': p.due_date.isoformat() if p.due_date else None,
                'status': p.status.value,
                'pago_em': p.paid_date.isoformat() if p.paid_date else None,
            })

    # Agendamentos
    for b in user.bookings if hasattr(user, 'bookings') else []:
        data['agendamentos'].append({
            'data': b.date.isoformat() if b.date else None,
            'horario': b.time.isoformat() if hasattr(b, 'time') and b.time else None,
            'status': b.status.value,
        })

    # Consentimentos
    from app.models.consent_log import ConsentLog
    for cl in ConsentLog.query.filter_by(user_id=user_id).all():
        data['consentimentos'].append({
            'tipo': cl.consent_type.value,
            'aceito': cl.accepted,
            'data': cl.created_at.isoformat() if cl.created_at else None,
            'revogado': cl.revoked_at.isoformat() if cl.revoked_at else None,
        })

    # Registrar auditoria
    AuditLog.log(
        action=AuditAction.DATA_EXPORT,
        user_id=current_user.id,
        entity_type='User',
        entity_id=user_id,
        description=f'Dados exportados por {current_user.name}',
        ip_address=request.remote_addr
    )
    db.session.commit()

    from flask import make_response
    response = make_response(json.dumps(data, ensure_ascii=False, indent=2))
    response.headers['Content-Type'] = 'application/json; charset=utf-8'
    response.headers['Content-Disposition'] = f'attachment; filename=dados_usuario_{user_id}.json'
    return response
