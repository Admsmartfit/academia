# app/routes/admin/modalities.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.models import Modality
from app import db
from app.routes.admin.dashboard import admin_required

modalities_bp = Blueprint('admin_modalities', __name__, url_prefix='/admin/modalities')


@modalities_bp.route('/')
@login_required
@admin_required
def list_modalities():
    """Lista todas as modalidades"""
    modalities = Modality.query.order_by(Modality.name).all()
    return render_template('admin/modalities/list.html', modalities=modalities)


@modalities_bp.route('/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_modality():
    """Criar nova modalidade"""
    if request.method == 'POST':
        modality = Modality(
            name=request.form['name'],
            description=request.form.get('description'),
            color=request.form.get('color', '#FF6B35'),
            icon=request.form.get('icon'),
            credits_cost=int(request.form.get('credits_cost', 1)),
            is_active=True
        )

        db.session.add(modality)
        db.session.commit()

        flash(f'Modalidade "{modality.name}" criada com sucesso!', 'success')
        return redirect(url_for('admin_modalities.list_modalities'))

    return render_template('admin/modalities/form.html', modality=None)


@modalities_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_modality(id):
    """Editar modalidade existente"""
    modality = Modality.query.get_or_404(id)

    if request.method == 'POST':
        modality.name = request.form['name']
        modality.description = request.form.get('description')
        modality.color = request.form.get('color', '#FF6B35')
        modality.icon = request.form.get('icon')
        modality.credits_cost = int(request.form.get('credits_cost', 1))

        db.session.commit()

        flash(f'Modalidade "{modality.name}" atualizada!', 'success')
        return redirect(url_for('admin_modalities.list_modalities'))

    return render_template('admin/modalities/form.html', modality=modality)


@modalities_bp.route('/toggle/<int:id>', methods=['POST'])
@login_required
@admin_required
def toggle_modality(id):
    """Ativar/desativar modalidade"""
    modality = Modality.query.get_or_404(id)
    modality.is_active = not modality.is_active
    db.session.commit()

    status = "ativada" if modality.is_active else "desativada"
    flash(f'Modalidade "{modality.name}" {status}.', 'info')
    return redirect(url_for('admin_modalities.list_modalities'))


@modalities_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_modality(id):
    """Deletar modalidade (se nao tiver horarios associados)"""
    modality = Modality.query.get_or_404(id)

    if modality.schedules:
        flash(f'Nao e possivel excluir "{modality.name}" pois existem horarios associados.', 'danger')
        return redirect(url_for('admin_modalities.list_modalities'))

    db.session.delete(modality)
    db.session.commit()

    flash(f'Modalidade "{modality.name}" excluida.', 'info')
    return redirect(url_for('admin_modalities.list_modalities'))
