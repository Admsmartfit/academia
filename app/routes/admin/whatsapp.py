# app/routes/admin/whatsapp.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models import WhatsAppTemplate, WhatsAppLog, TemplateCategory, TemplateTrigger
from app import db
from app.routes.admin.dashboard import admin_required
import re

whatsapp_bp = Blueprint('admin_whatsapp', __name__, url_prefix='/admin/whatsapp')


@whatsapp_bp.route('/templates')
@login_required
@admin_required
def list_templates():
    """Lista todos os templates"""
    templates = WhatsAppTemplate.query.order_by(WhatsAppTemplate.trigger).all()
    return render_template('admin/whatsapp/templates.html', templates=templates)


@whatsapp_bp.route('/templates/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_template():
    """Criar novo template"""
    if request.method == 'POST':
        # Extrair variaveis do conteudo
        content = request.form['content']
        variables = re.findall(r'\{\{(\d+)\}\}', content)

        template = WhatsAppTemplate(
            name=request.form['name'],
            template_code=request.form['template_code'],
            category=TemplateCategory[request.form['category']],
            trigger=TemplateTrigger[request.form['trigger']],
            content=content,
            variables=[f'{{{{{v}}}}}' for v in variables],
            megaapi_status='pending',
            is_active=False  # Ativar so apos aprovacao Megaapi
        )

        db.session.add(template)
        db.session.commit()

        flash(f'Template "{template.name}" criado! Aguardando aprovacao da Megaapi.', 'info')
        return redirect(url_for('admin_whatsapp.list_templates'))

    return render_template('admin/whatsapp/template_form.html',
                           template=None,
                           categories=TemplateCategory,
                           triggers=TemplateTrigger)


@whatsapp_bp.route('/templates/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_template(id):
    """Editar template"""
    template = WhatsAppTemplate.query.get_or_404(id)

    if request.method == 'POST':
        content = request.form['content']
        old_content = template.content
        variables = re.findall(r'\{\{(\d+)\}\}', content)

        template.name = request.form['name']
        template.content = content
        template.variables = [f'{{{{{v}}}}}' for v in variables]
        template.category = TemplateCategory[request.form['category']]
        template.trigger = TemplateTrigger[request.form['trigger']]

        # Se mudou conteudo, precisa reenviar para aprovacao
        if old_content != content:
            template.megaapi_status = 'pending'
            template.is_active = False

        db.session.commit()

        flash(f'Template "{template.name}" atualizado!', 'success')
        return redirect(url_for('admin_whatsapp.list_templates'))

    return render_template('admin/whatsapp/template_form.html',
                           template=template,
                           categories=TemplateCategory,
                           triggers=TemplateTrigger)


@whatsapp_bp.route('/templates/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_template(id):
    """Desativar template"""
    template = WhatsAppTemplate.query.get_or_404(id)
    template.is_active = False
    db.session.commit()

    flash(f'Template "{template.name}" desativado.', 'info')
    return redirect(url_for('admin_whatsapp.list_templates'))


@whatsapp_bp.route('/templates/activate/<int:id>', methods=['POST'])
@login_required
@admin_required
def activate_template(id):
    """Ativar template (se aprovado)"""
    template = WhatsAppTemplate.query.get_or_404(id)

    if template.megaapi_status != 'approved':
        flash('Template precisa ser aprovado pela Megaapi antes de ativar.', 'warning')
        return redirect(url_for('admin_whatsapp.list_templates'))

    template.is_active = True
    db.session.commit()

    flash(f'Template "{template.name}" ativado!', 'success')
    return redirect(url_for('admin_whatsapp.list_templates'))


@whatsapp_bp.route('/templates/test/<int:id>', methods=['POST'])
@login_required
@admin_required
def test_template(id):
    """Enviar template de teste para o proprio admin"""
    template = WhatsAppTemplate.query.get_or_404(id)

    if template.megaapi_status != 'approved':
        return jsonify({'error': 'Template nao aprovado pela Megaapi'}), 400

    # Variaveis de teste
    test_vars = [
        current_user.name.split()[0],
        'Teste',
        '100.00',
        'Academia Teste',
        '31/01/2026'
    ]

    try:
        from app.services.megaapi import megaapi

        megaapi.send_template_message(
            phone=current_user.phone,
            template_name=template.template_code,
            variables=test_vars[:len(template.variables)],
            user_id=current_user.id
        )

        return jsonify({'success': True, 'message': 'Mensagem de teste enviada!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@whatsapp_bp.route('/templates/sync-status', methods=['POST'])
@login_required
@admin_required
def sync_megaapi_status():
    """Sincronizar status dos templates com Megaapi"""
    templates = WhatsAppTemplate.query.filter_by(megaapi_status='pending').all()

    updated = 0
    for template in templates:
        try:
            from app.services.megaapi import megaapi

            # Consultar status na Megaapi
            status = megaapi.get_template_status(template.template_code)

            if status == 'approved':
                template.megaapi_status = 'approved'
                template.is_active = True
                updated += 1
            elif status == 'rejected':
                template.megaapi_status = 'rejected'

            db.session.commit()
        except:
            pass

    flash(f'{updated} template(s) aprovado(s)!', 'success')
    return redirect(url_for('admin_whatsapp.list_templates'))


@whatsapp_bp.route('/templates/approve/<int:id>', methods=['POST'])
@login_required
@admin_required
def manual_approve_template(id):
    """Aprovar template manualmente (para testes locais)"""
    template = WhatsAppTemplate.query.get_or_404(id)
    template.megaapi_status = 'approved'
    template.is_active = True
    db.session.commit()

    flash(f'Template "{template.name}" aprovado manualmente!', 'success')
    return redirect(url_for('admin_whatsapp.list_templates'))


@whatsapp_bp.route('/flows')
@login_required
@admin_required
def interactive_flows():
    """Painel dos 6 Fluxos Interativos PRD com status e métricas."""
    from app.models.crm import AutomationLog
    from sqlalchemy import func
    from datetime import timedelta

    # Buscar fluxos PRD
    prd_flows = WhatsAppTemplate.query.filter_by(is_prd_flow=True).all()

    # Montar métricas para cada fluxo
    flows_data = []
    thirty_days_ago = db.func.now() - timedelta(days=30)

    for flow in prd_flows:
        # Contar envios (30 dias)
        sends_30d = flow.send_count or 0

        # Tipo de interação
        type_label = {
            'buttons': 'Botões',
            'list': 'Lista',
            'text': 'Texto simples',
            'template': 'Template'
        }.get(flow.message_type, 'Template')

        # Botões/opções configurados
        buttons = []
        if flow.buttons_config:
            if 'buttons' in flow.buttons_config:
                buttons = [b['title'] for b in flow.buttons_config['buttons']]
            elif 'sections' in flow.buttons_config:
                for section in flow.buttons_config['sections']:
                    for row in section.get('rows', []):
                        buttons.append(row['title'])

        flows_data.append({
            'id': flow.id,
            'name': flow.name,
            'trigger': flow.trigger.value,
            'content': flow.content,
            'message_type': flow.message_type,
            'type_label': type_label,
            'buttons': buttons,
            'is_active': flow.is_active,
            'status': flow.megaapi_status or 'pending',
            'sends_30d': sends_30d,
            'template_code': flow.template_code
        })

    return render_template('admin/whatsapp/flows.html', flows=flows_data)


@whatsapp_bp.route('/flows/toggle/<int:id>', methods=['POST'])
@login_required
@admin_required
def toggle_flow(id):
    """Ativar/desativar fluxo PRD."""
    flow = WhatsAppTemplate.query.get_or_404(id)
    flow.is_active = not flow.is_active
    db.session.commit()

    status = 'ativado' if flow.is_active else 'desativado'
    flash(f'Fluxo "{flow.name}" {status}!', 'success')
    return redirect(url_for('admin_whatsapp.interactive_flows'))


@whatsapp_bp.route('/logs')
@login_required
@admin_required
def list_logs():
    """Lista logs de mensagens enviadas"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')

    query = WhatsAppLog.query

    if status_filter:
        query = query.filter_by(status=status_filter)

    logs = query.order_by(WhatsAppLog.sent_at.desc()).paginate(
        page=page, per_page=50, error_out=False
    )

    return render_template('admin/whatsapp/logs.html', logs=logs, status_filter=status_filter)
