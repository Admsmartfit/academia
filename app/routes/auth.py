# app/routes/auth.py

import re
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User, Gender
from app import db
from datetime import datetime

auth_bp = Blueprint('auth', __name__)


def validate_phone(phone: str) -> str:
    """
    Valida e formata telefone para padrao 5511999999999

    Args:
        phone: Numero de telefone em qualquer formato

    Returns:
        Telefone formatado (5511999999999)

    Raises:
        ValueError: Se o telefone for invalido
    """
    # Remover tudo que nao e numero
    clean = re.sub(r'\D', '', phone)

    # Adicionar codigo do pais se nao tiver
    if not clean.startswith('55'):
        clean = '55' + clean

    # Validar tamanho (55 + DDD + 9 digitos = 13)
    if len(clean) != 13:
        raise ValueError('Telefone invalido. Use: (11) 99999-9999')

    # Validar DDD (11-99)
    ddd = int(clean[2:4])
    if ddd < 11 or ddd > 99:
        raise ValueError('DDD invalido.')

    return clean


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Pagina de login"""
    if current_user.is_authenticated:
        if current_user.role == 'totem':
            return redirect(url_for('instructor.totem_view'))
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

            # Usuario de terminal vai direto para o totem
            if user.role == 'totem':
                return redirect(url_for('instructor.totem_view'))

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

    # Capturar parametro trial para rastrear origem da landing page
    trial_type = request.args.get('trial')
    show_fes_banner = (trial_type == 'fes')

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        cpf = request.form.get('cpf', '').strip()
        gender_str = request.form.get('gender', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        trial_type = request.form.get('trial_type', '')

        # Validacoes
        errors = []

        if not name or len(name) < 3:
            errors.append('Nome deve ter pelo menos 3 caracteres.')

        if not email or '@' not in email:
            errors.append('E-mail invalido.')

        if User.query.filter_by(email=email).first():
            errors.append('Este e-mail ja esta cadastrado.')

        # Validar CPF
        if not cpf:
            errors.append('O CPF é obrigatório.')
        elif not User.validate_cpf(cpf):
            errors.append('CPF inválido.')

        # Validar sexo
        gender = None
        if gender_str:
            if gender_str == 'male':
                gender = Gender.MALE
            elif gender_str == 'female':
                gender = Gender.FEMALE
            else:
                errors.append('Sexo inválido.')

        # Validar e formatar telefone
        phone_formatted = None
        try:
            phone_formatted = validate_phone(phone)
        except ValueError as e:
            errors.append(str(e))

        if len(password) < 6:
            errors.append('Senha deve ter pelo menos 6 caracteres.')

        if password != confirm_password:
            errors.append('As senhas nao conferem.')

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('auth/register.html',
                trial_type=trial_type,
                show_fes_banner=show_fes_banner)

        # Criar usuario
        user = User(
            name=name,
            email=email,
            phone=phone_formatted,
            cpf=User.format_cpf(cpf),
            gender=gender,
            role='student',
            is_active=True
        )
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        flash('Conta criada com sucesso! Faca login para continuar.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html',
        trial_type=trial_type,
        show_fes_banner=show_fes_banner)


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
