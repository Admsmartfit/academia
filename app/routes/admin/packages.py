# app/routes/admin/packages.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.models import Package
from app import db
from app.services.image_handler import save_package_image
from app.routes.admin.dashboard import admin_required
from decimal import Decimal

packages_bp = Blueprint('admin_packages', __name__, url_prefix='/admin/packages')


@packages_bp.route('/')
@login_required
@admin_required
def list_packages():
    """Lista todos os pacotes"""
    packages = Package.query.order_by(Package.display_order, Package.id).all()
    return render_template('admin/packages/list.html', packages=packages)


@packages_bp.route('/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_package():
    """Criar novo pacote"""
    if request.method == 'POST':
        # Processar upload de imagem
        photo_url = None
        if 'photo' in request.files:
            file = request.files['photo']
            if file.filename:
                try:
                    photo_url = save_package_image(file)
                except ValueError as e:
                    flash(str(e), 'danger')
                    return render_template('admin/packages/form.html', package=None)

        # Calcular preco da parcela
        price = Decimal(request.form['price'])
        installments = int(request.form['installments'])
        installment_price = price / installments

        # Processar beneficios extras
        benefits_raw = request.form.get('extra_benefits', '')
        extra_benefits = [b.strip() for b in benefits_raw.split('\n') if b.strip()]

        package = Package(
            name=request.form['name'],
            description=request.form.get('description'),
            credits=int(request.form['credits']),
            price=price,
            installments=installments,
            installment_price=installment_price,
            validity_days=int(request.form['validity_days']),
            photo_url=photo_url,
            color=request.form.get('color', '#FF6B35'),
            is_featured=bool(request.form.get('is_featured')),
            display_order=int(request.form.get('display_order', 0)),
            extra_benefits=extra_benefits if extra_benefits else None,
            is_active=True
        )

        db.session.add(package)
        db.session.commit()

        flash(f'Pacote "{package.name}" criado com sucesso!', 'success')
        return redirect(url_for('admin_packages.list_packages'))

    return render_template('admin/packages/form.html', package=None)


@packages_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_package(id):
    """Editar pacote existente"""
    package = Package.query.get_or_404(id)

    if request.method == 'POST':
        # Atualizar imagem se enviada
        if 'photo' in request.files:
            file = request.files['photo']
            if file.filename:
                try:
                    package.photo_url = save_package_image(file)
                except ValueError as e:
                    flash(str(e), 'danger')
                    return render_template('admin/packages/form.html', package=package)

        price = Decimal(request.form['price'])
        installments = int(request.form['installments'])

        package.name = request.form['name']
        package.description = request.form.get('description')
        package.credits = int(request.form['credits'])
        package.price = price
        package.installments = installments
        package.installment_price = price / installments
        package.validity_days = int(request.form['validity_days'])
        package.color = request.form.get('color', '#FF6B35')
        package.is_featured = bool(request.form.get('is_featured'))
        package.display_order = int(request.form.get('display_order', 0))

        # Beneficios
        benefits_raw = request.form.get('extra_benefits', '')
        extra_benefits = [b.strip() for b in benefits_raw.split('\n') if b.strip()]
        package.extra_benefits = extra_benefits if extra_benefits else None

        db.session.commit()

        flash(f'Pacote "{package.name}" atualizado!', 'success')
        return redirect(url_for('admin_packages.list_packages'))

    return render_template('admin/packages/form.html', package=package)


@packages_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_package(id):
    """Desativar pacote"""
    package = Package.query.get_or_404(id)
    package.is_active = False
    db.session.commit()

    flash(f'Pacote "{package.name}" desativado.', 'info')
    return redirect(url_for('admin_packages.list_packages'))


@packages_bp.route('/toggle/<int:id>', methods=['POST'])
@login_required
@admin_required
def toggle_package(id):
    """Ativar/desativar pacote"""
    package = Package.query.get_or_404(id)
    package.is_active = not package.is_active
    db.session.commit()

    status = "ativado" if package.is_active else "desativado"
    flash(f'Pacote "{package.name}" {status}.', 'info')
    return redirect(url_for('admin_packages.list_packages'))
