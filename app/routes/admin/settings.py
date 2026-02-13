# app/routes/admin/settings.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.routes.admin.dashboard import admin_required
from app.models import SystemConfig
from app import db


settings_bp = Blueprint('admin_settings', __name__, url_prefix='/admin/settings')


@settings_bp.route('/', methods=['GET', 'POST'])
@login_required
@admin_required
def index():
    """Pagina de configuracoes do sistema"""

    if request.method == 'POST':
        # Atualizar configuracoes
        credits_per_real = request.form.get('credits_per_real', '1')
        academy_name = request.form.get('academy_name', 'Academia Fitness')
        academy_address = request.form.get('academy_address', '')
        cancellation_hours = request.form.get('cancellation_hours', '2')

        # Validar credits_per_real
        try:
            credits_value = float(credits_per_real)
            if credits_value <= 0:
                raise ValueError("Valor deve ser maior que zero")
        except ValueError:
            flash('Creditos por Real deve ser um numero positivo.', 'danger')
            return redirect(url_for('admin_settings.index'))

        # Validar cancellation_hours
        try:
            cancel_hours = int(cancellation_hours)
            if cancel_hours < 0 or cancel_hours > 48:
                raise ValueError("Valor deve estar entre 0 e 48")
        except ValueError:
            flash('Horas de cancelamento deve ser um numero entre 0 e 48.', 'danger')
            return redirect(url_for('admin_settings.index'))

        # Salvar configuracoes
        SystemConfig.set('credits_per_real', credits_per_real, 'Quantidade de creditos por cada R$1,00')
        SystemConfig.set('academy_name', academy_name, 'Nome da academia')
        SystemConfig.set('academy_address', academy_address, 'Endereco da academia')
        SystemConfig.set('cancellation_hours', cancellation_hours, 'Horas minimas de antecedencia para cancelar aula')

        flash('Configuracoes salvas com sucesso!', 'success')
        return redirect(url_for('admin_settings.index'))

    # Buscar configuracoes atuais
    configs = SystemConfig.get_all()

    return render_template('admin/settings/index.html', configs=configs)


@settings_bp.route('/credits-calculator')
@login_required
@admin_required
def credits_calculator():
    """API para calcular creditos baseado no preco"""
    price = request.args.get('price', 0, type=float)
    credits = SystemConfig.calculate_credits(price)
    credits_per_real = SystemConfig.get_float('credits_per_real', 1.0)

    return {
        'price': price,
        'credits': credits,
        'credits_per_real': credits_per_real
    }


@settings_bp.route('/notifications')
@login_required
@admin_required
def notifications():
    """Aba de notificacoes - creditos expirando"""
    from datetime import datetime, timedelta
    from app.models.credit_wallet import CreditWallet

    target_date = datetime.now() + timedelta(days=7)

    wallets = CreditWallet.query.filter(
        CreditWallet.is_expired == False,
        CreditWallet.credits_remaining > 0,
        CreditWallet.expires_at <= target_date,
        CreditWallet.expires_at > datetime.now()
    ).all()

    # Agrupar por usuario
    user_expiring = {}
    for wallet in wallets:
        if wallet.user_id not in user_expiring:
            user_expiring[wallet.user_id] = {
                'user': wallet.user,
                'credits': 0,
                'earliest_expiry': wallet.expires_at,
                'days': wallet.days_until_expiry
            }
        user_expiring[wallet.user_id]['credits'] += wallet.credits_remaining
        if wallet.expires_at < user_expiring[wallet.user_id]['earliest_expiry']:
            user_expiring[wallet.user_id]['earliest_expiry'] = wallet.expires_at
            user_expiring[wallet.user_id]['days'] = wallet.days_until_expiry

    expiring_list = sorted(user_expiring.values(), key=lambda x: x['days'])

    return render_template('admin/settings/notifications.html',
                           expiring_list=expiring_list,
                           total_expiring=len(expiring_list))


@settings_bp.route('/notifications/send', methods=['POST'])
@login_required
@admin_required
def send_expiring_notifications():
    """Dispara notificacoes de creditos expirando via WhatsApp"""
    from datetime import datetime, timedelta
    from app.models.credit_wallet import CreditWallet
    from app.services.notification_service import NotificationService

    target_date = datetime.now() + timedelta(days=7)

    wallets = CreditWallet.query.filter(
        CreditWallet.is_expired == False,
        CreditWallet.credits_remaining > 0,
        CreditWallet.expires_at <= target_date,
        CreditWallet.expires_at > datetime.now()
    ).all()

    user_expiring = {}
    for wallet in wallets:
        if wallet.user_id not in user_expiring:
            user_expiring[wallet.user_id] = {
                'credits': 0,
                'earliest_expiry': wallet.expires_at,
                'days': wallet.days_until_expiry
            }
        user_expiring[wallet.user_id]['credits'] += wallet.credits_remaining
        if wallet.expires_at < user_expiring[wallet.user_id]['earliest_expiry']:
            user_expiring[wallet.user_id]['earliest_expiry'] = wallet.expires_at
            user_expiring[wallet.user_id]['days'] = wallet.days_until_expiry

    sent = 0
    errors = 0
    for user_id, info in user_expiring.items():
        if info['credits'] >= 1:
            try:
                NotificationService.notify_credits_expiring(
                    user_id=user_id,
                    credits_amount=info['credits'],
                    days_remaining=info['days'],
                    expires_at=info['earliest_expiry']
                )
                sent += 1
            except Exception:
                errors += 1

    from flask import jsonify
    return jsonify({
        'success': True,
        'sent': sent,
        'errors': errors,
        'message': f'{sent} notificacao(oes) enviada(s), {errors} erro(s).'
    })
