# app/routes/admin/users.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models import User
from app import db
from app.routes.admin.dashboard import admin_required
from app.routes.auth import validate_phone

users_bp = Blueprint('admin_users', __name__, url_prefix='/admin/users')


# =============================================================================
# Roles disponiveis no sistema
# =============================================================================
AVAILABLE_ROLES = ['student', 'instructor', 'admin', 'totem']

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
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password')
        role = request.form.get('role', 'student')

        if User.query.filter_by(email=email).first():
            flash('Este e-mail já está cadastrado.', 'danger')
            return redirect(url_for('admin_users.create_user'))

        # Validar telefone
        phone_formatted = phone
        if phone:
            try:
                phone_formatted = validate_phone(phone)
            except ValueError as e:
                flash(str(e), 'danger')
                return redirect(url_for('admin_users.create_user'))

        user = User(
            name=name,
            email=email,
            phone=phone_formatted,
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
        phone = request.form.get('phone', '').strip()
        phone_formatted = phone
        if phone:
            try:
                phone_formatted = validate_phone(phone)
            except ValueError as e:
                flash(str(e), 'danger')
                return redirect(url_for('admin_users.edit_user', id=id))

        user.name = request.form.get('name')
        user.email = request.form.get('email', '').strip().lower()
        user.phone = phone_formatted
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


# =============================================================================
# Cadastro Facial (Admin)
# =============================================================================

@users_bp.route('/<int:id>/face', methods=['GET'])
@login_required
@admin_required
def face_enrollment(id):
    """Pagina de cadastro facial para qualquer usuario (admin only)."""
    user = User.query.get_or_404(id)
    return render_template('admin/users/face_enrollment.html', user=user)


@users_bp.route('/<int:id>/face/enroll', methods=['POST'])
@login_required
@admin_required
def enroll_face_admin(id):
    """API para admin cadastrar face de qualquer usuario."""
    from app.services.face_service import FaceRecognitionService

    user = User.query.get_or_404(id)
    data = request.get_json()

    if not data or 'image' not in data:
        return jsonify({
            'success': False,
            'error': 'Imagem nao fornecida'
        }), 400

    face_service = FaceRecognitionService(tolerance=0.6)
    result = face_service.enroll_face(user.id, data['image'])

    if result['success']:
        return jsonify({
            'success': True,
            'message': f'Face de {user.name} cadastrada com sucesso!',
            'confidence': result['confidence']
        }), 201
    else:
        return jsonify({
            'success': False,
            'error': result['message']
        }), 400


@users_bp.route('/<int:id>/face/remove', methods=['POST'])
@login_required
@admin_required
def remove_face_admin(id):
    """Remove face de um usuario (admin only)."""
    from app.services.face_service import FaceRecognitionService

    user = User.query.get_or_404(id)
    face_service = FaceRecognitionService()
    result = face_service.remove_face(user.id)

    if result['success']:
        flash(f'Face de {user.name} removida com sucesso!', 'success')
    else:
        flash(result['message'], 'warning')

    return redirect(url_for('admin_users.face_enrollment', id=id))


# =============================================================================
# Usuario Totem (Terminal de Check-in)
# =============================================================================

@users_bp.route('/create-totem', methods=['GET', 'POST'])
@login_required
@admin_required
def create_totem_user():
    """Cria um usuario especial para terminal de check-in facial."""
    if request.method == 'POST':
        name = request.form.get('name', 'Terminal Check-in')
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password')

        if not email or not password:
            flash('Email e senha sao obrigatorios.', 'danger')
            return redirect(url_for('admin_users.create_totem_user'))

        if User.query.filter_by(email=email).first():
            flash('Este e-mail ja esta cadastrado.', 'danger')
            return redirect(url_for('admin_users.create_totem_user'))

        user = User(
            name=name,
            email=email,
            phone='',
            role='totem',
            is_active=True
        )
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        flash(f'Usuario de terminal "{name}" criado! Use {email} para acessar o totem.', 'success')
        return redirect(url_for('admin_users.list_users', role='totem'))

    return render_template('admin/users/totem_form.html')
