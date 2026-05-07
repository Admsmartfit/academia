# app/routes/admin/megaapi_config.py

import requests
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required
from app.routes.admin.dashboard import admin_required
from app.services.megaapi import megaapi


megaapi_config_bp = Blueprint('admin_megaapi', __name__, url_prefix='/admin/megaapi')


def get_instance_status(host=None, token=None, instance_key=None) -> dict:
    """
    Busca status da instancia MegaAPI adaptado para servidores Start/Dedicated.
    """
    base_url = (host or megaapi.base_url or '').rstrip('/')
    current_token = token or megaapi.token
    current_instance_key = instance_key or getattr(megaapi, 'instance_key', None)

    if not base_url or not current_token or not current_instance_key:
        return {'connected': False, 'error': 'Credenciais ou Instance Key incompletas'}

    headers = {
        'Authorization': f'Bearer {current_token}',
        'Content-Type': 'application/json'
    }

    try:
        endpoint_url = f"{base_url}/instance/status/{current_instance_key}"

        response = requests.get(
            endpoint_url,
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            is_online = data.get('status') == 'online' or data.get('instance', {}).get('state') == 'open'
            return {
                'connected': True,
                'status': 'Online' if is_online else 'Desconectado',
                'data': data
            }
        elif response.status_code == 404:
            return {
                'connected': False,
                'error': f'Erro 404: O servidor não encontrou a instância "{current_instance_key}". Verifique se a Instance Key está correta.'
            }
        else:
            return {
                'connected': False,
                'error': f'Erro HTTP {response.status_code} no servidor MegaAPI.'
            }

    except Exception as e:
        return {'connected': False, 'error': f"Falha de rede: {str(e)}"}


@megaapi_config_bp.route('/check-status', methods=['POST'])
@login_required
@admin_required
def check_status_ajax():
    """Verifica status via AJAX (real-time validation)"""
    # Se receber dados no form, atualiza temporariamente a instancia para teste
    if request.json:
        temp_host = request.json.get('host')
        temp_token = request.json.get('token')
        temp_key = request.json.get('instance_key')
        
        # Backup
        original_host = megaapi.base_url
        original_token = megaapi.token
        original_key = getattr(megaapi, 'instance_key', None)
        original_headers = megaapi.headers
        
        # Apply Temp
        if temp_host: megaapi.base_url = temp_host.rstrip('/')
        if temp_token: 
            megaapi.token = temp_token
            megaapi.headers = {
                'Authorization': f'Bearer {temp_token}',
                'Content-Type': 'application/json'
            }
        if temp_key: megaapi.instance_key = temp_key
        
        # Check
        status = get_instance_status()
        
        # Restore
        megaapi.base_url = original_host
        megaapi.token = original_token
        megaapi.instance_key = original_key
        megaapi.headers = original_headers
        
        return jsonify(status)
        
    return jsonify(get_instance_status())

@megaapi_config_bp.route('/', methods=['GET', 'POST'])
@login_required
@admin_required
def settings():
    """Pagina de configuracao da MegaAPI"""

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'save_config':
            # Atualizar configuracoes em memoria
            new_host = request.form.get('host', '').strip()
            new_token = request.form.get('token', '').strip()
            new_instance_key = request.form.get('instance_key', '').strip()

            if new_host:
                # Remover barra final se existir
                megaapi.base_url = new_host.rstrip('/')

            if new_token:
                megaapi.token = new_token
                megaapi.headers = {
                    'Authorization': f'Bearer {new_token}',
                    'Content-Type': 'application/json'
                }

            if new_instance_key:
                megaapi.instance_key = new_instance_key

            flash('Configuracoes atualizadas com sucesso!', 'success')
            return redirect(url_for('admin_megaapi.settings'))

        elif action == 'send_test':
            # Enviar mensagem de teste
            phone = request.form.get('test_phone', '').strip()
            message = request.form.get('test_message', '').strip()

            if not phone or not message:
                flash('Preencha o telefone e a mensagem', 'warning')
                return redirect(url_for('admin_megaapi.settings'))

            try:
                result = megaapi.send_custom_message(
                    phone=phone,
                    message=message
                )
                flash(f'Mensagem enviada com sucesso! ID: {result.get("id", "N/A")}', 'success')
            except ValueError as e:
                flash(f'Erro no telefone: {str(e)}', 'danger')
            except Exception as e:
                flash(f'Erro ao enviar: {str(e)}', 'danger')

            return redirect(url_for('admin_megaapi.settings'))

    # GET - Buscar status da instancia
    instance_status = get_instance_status()

    return render_template('admin/megaapi/settings.html',
        instance_status=instance_status,
        current_host=megaapi.base_url or '',
        current_token=megaapi.token or '',
        current_instance_key=getattr(megaapi, 'instance_key', '') or ''
    )
