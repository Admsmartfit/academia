# app/routes/admin/nupay_config.py

import requests
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required
from app.routes.admin.dashboard import admin_required
from app.models import SystemConfig
from app.services.nupay import NuPayService


nupay_config_bp = Blueprint('admin_nupay', __name__, url_prefix='/admin/nupay')


@nupay_config_bp.route('/', methods=['GET', 'POST'])
@login_required
@admin_required
def settings():
    """Pagina de configuracao da NuPay"""

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'save_config':
            # Atualizar configuracoes no banco
            new_host = request.form.get('host', '').strip()
            new_key = request.form.get('merchant_key', '').strip()
            new_token = request.form.get('merchant_token', '').strip()
            new_secret = request.form.get('webhook_secret', '').strip()

            if new_host:
                SystemConfig.set('nupay_base_url', new_host, 'URL base da API NuPay')
            
            if new_key:
                SystemConfig.set('nupay_merchant_key', new_key, 'Chave de lojista NuPay (X-Merchant-Key)')
            
            if new_token:
                SystemConfig.set('nupay_merchant_token', new_token, 'Token de lojista NuPay (X-Merchant-Token)')
            
            if new_secret:
                SystemConfig.set('nupay_webhook_secret', new_secret, 'Segredo para validacao de webhook NuPay')

            flash('Configuracoes da NuPay atualizadas com sucesso!', 'success')
            return redirect(url_for('admin_nupay.settings'))

        elif action == 'test_connection':
            # Testar conexao com a NuPay
            try:
                # Criar instancia do servico (que usara as novas configs se ja salvas ou passadas)
                nupay = NuPayService()
                
                # Vamos tentar buscar um status de pagamento aleatorio apenas para testar headers
                # A API NuPay nao tem um endpoint de "ping" obvio, mas podemos tentar listar algo
                # ou usar o merchant key para validar.
                
                response = requests.get(
                    f"{nupay.base_url}/v1/checkouts/payments/test_ping",
                    headers=nupay.headers,
                    timeout=10
                )
                
                # Se retornar 404, significa que os headers foram aceitos mas o ID nao existe (o que e bom)
                # Se retornar 401, as chaves estao erradas
                if response.status_code == 404:
                    flash('Conexao com NuPay validada! (Endpoint respondeu corretamente)', 'success')
                elif response.status_code == 401:
                    flash('Erro de autenticacao: Verifique seu Merchant Key e Token.', 'danger')
                else:
                    flash(f'Resposta da NuPay: Status {response.status_code}', 'info')
                    
            except Exception as e:
                flash(f'Erro ao testar conexao: {str(e)}', 'danger')
            
            return redirect(url_for('admin_nupay.settings'))

    # GET - Buscar configuracoes atuais
    configs = {
        'host': SystemConfig.get('nupay_base_url', current_app.config.get('NUPAY_BASE_URL', 'https://api.spinpay.com.br')),
        'merchant_key': SystemConfig.get('nupay_merchant_key', current_app.config.get('NUPAY_MERCHANT_KEY', '')),
        'merchant_token': SystemConfig.get('nupay_merchant_token', current_app.config.get('NUPAY_MERCHANT_TOKEN', '')),
        'webhook_secret': SystemConfig.get('nupay_webhook_secret', current_app.config.get('NUPAY_WEBHOOK_SECRET', '')),
    }

    return render_template('admin/nupay/settings.html', configs=configs)
