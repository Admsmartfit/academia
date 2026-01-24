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
