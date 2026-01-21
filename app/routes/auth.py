# app/routes/auth.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User
from app import db
from datetime import datetime

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Pagina de login"""
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('student.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            if not user.is_active:
                flash('Sua conta esta desativada. Entre em contato com a academia.', 'danger')
                return render_template('auth/login.html')

            login_user(user, remember=remember)
            user.last_login = datetime.utcnow()
            db.session.commit()

            flash(f'Bem-vindo(a), {user.name}!', 'success')

            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)

            if user.is_admin:
                return redirect(url_for('admin.dashboard'))
            if user.is_instructor:
                return redirect(url_for('instructor.dashboard'))
            return redirect(url_for('student.dashboard'))

        flash('E-mail ou senha invalidos.', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Pagina de registro de novo aluno"""
    if current_user.is_authenticated:
        return redirect(url_for('student.dashboard'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Validacoes
        errors = []

        if not name or len(name) < 3:
            errors.append('Nome deve ter pelo menos 3 caracteres.')

        if not email or '@' not in email:
            errors.append('E-mail invalido.')

        if User.query.filter_by(email=email).first():
            errors.append('Este e-mail ja esta cadastrado.')

        if not phone or len(phone) < 10:
            errors.append('Telefone invalido.')

        if len(password) < 6:
            errors.append('Senha deve ter pelo menos 6 caracteres.')

        if password != confirm_password:
            errors.append('As senhas nao conferem.')

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('auth/register.html')

        # Criar usuario
        user = User(
            name=name,
            email=email,
            phone=phone,
            role='student',
            is_active=True
        )
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        flash('Conta criada com sucesso! Faca login para continuar.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """Logout do usuario"""
    logout_user()
    flash('Voce saiu do sistema.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Recuperacao de senha (placeholder)"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        user = User.query.filter_by(email=email).first()

        if user:
            # TODO: Implementar envio de e-mail ou WhatsApp
            flash('Se o e-mail existir, voce recebera instrucoes para redefinir sua senha.', 'info')
        else:
            flash('Se o e-mail existir, voce recebera instrucoes para redefinir sua senha.', 'info')

        return redirect(url_for('auth.login'))

    return render_template('auth/forgot_password.html')
