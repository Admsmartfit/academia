# app/routes/admin/users.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import User
from app import db
from app.routes.admin.dashboard import admin_required

users_bp = Blueprint('admin_users', __name__, url_prefix='/admin/users')

@users_bp.route('/')
@login_required
@admin_required
def list_users():
    """Lista todos os usuários"""
    role = request.args.get('role')
    if role:
        users = User.query.filter_by(role=role).order_by(User.name).all()
    else:
        users = User.query.order_by(User.role, User.name).all()
    
    return render_template('admin/users/list.html', users=users, role_filter=role)

@users_bp.route('/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    """Cria um novo usuário (Admin ou Instrutor)"""
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone')
        password = request.form.get('password')
        role = request.form.get('role', 'student')

        if User.query.filter_by(email=email).first():
            flash('Este e-mail já está cadastrado.', 'danger')
            return redirect(url_for('admin_users.create_user'))

        user = User(
            name=name,
            email=email,
            phone=phone,
            role=role,
            is_active=True
        )
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        flash(f'Usuário {name} criado com sucesso como {role}!', 'success')
        return redirect(url_for('admin_users.list_users', role=role))

    return render_template('admin/users/form.html', user=None)

@users_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(id):
    """Edita um usuário existente"""
    user = User.query.get_or_404(id)

    if request.method == 'POST':
        user.name = request.form.get('name')
        user.email = request.form.get('email', '').strip().lower()
        user.phone = request.form.get('phone')
        user.role = request.form.get('role')
        
        password = request.form.get('password')
        if password:
            user.set_password(password)

        db.session.commit()
        flash(f'Usuário {user.name} atualizado!', 'success')
        return redirect(url_for('admin_users.list_users'))

    return render_template('admin/users/form.html', user=user)

@users_bp.route('/toggle/<int:id>', methods=['POST'])
@login_required
@admin_required
def toggle_user(id):
    """Ativa/Desativa um usuário"""
    user = User.query.get_or_404(id)
    if user.id == current_user.id:
        flash('Você não pode desativar sua própria conta.', 'warning')
        return redirect(url_for('admin_users.list_users'))
        
    user.is_active = not user.is_active
    db.session.commit()
    
    status = "ativado" if user.is_active else "desativado"
    flash(f'Usuário {user.name} {status}!', 'info')
    return redirect(url_for('admin_users.list_users'))
