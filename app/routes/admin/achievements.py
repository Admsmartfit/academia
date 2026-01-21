# app/routes/admin/achievements.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from app.models import Achievement, CriteriaType, Modality, UserAchievement
from app import db
from app.services.image_handler import save_achievement_icon
from app.routes.admin.dashboard import admin_required

achievements_bp = Blueprint('admin_achievements', __name__, url_prefix='/admin/achievements')


@achievements_bp.route('/')
@login_required
@admin_required
def list_achievements():
    """Lista todas as conquistas"""
    achievements = Achievement.query.order_by(Achievement.created_at.desc()).all()
    return render_template('admin/achievements/list.html', achievements=achievements)


@achievements_bp.route('/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_achievement():
    """Criar nova conquista"""
    if request.method == 'POST':
        # Upload de icone
        icon_url = None
        if 'icon' in request.files:
            file = request.files['icon']
            if file.filename:
                try:
                    icon_url = save_achievement_icon(file)
                except ValueError as e:
                    flash(str(e), 'danger')
                    modalities = Modality.query.filter_by(is_active=True).all()
                    return render_template('admin/achievements/form.html',
                                           achievement=None,
                                           criteria_types=CriteriaType,
                                           modalities=modalities)

        # Processar extra (para modalidades especificas)
        criteria_extra = None
        if request.form['criteria_type'] == 'SPECIFIC_MODALITY':
            modality_id = request.form.get('modality_id')
            if modality_id:
                criteria_extra = {'modality_id': int(modality_id)}

        achievement = Achievement(
            name=request.form['name'],
            description=request.form.get('description'),
            icon_url=icon_url or request.form.get('icon_emoji'),
            criteria_type=CriteriaType[request.form['criteria_type']],
            criteria_value=int(request.form['criteria_value']),
            criteria_extra=criteria_extra,
            xp_reward=int(request.form.get('xp_reward', 0)),
            color=request.form.get('color', '#FFD700'),
            is_active=True
        )

        db.session.add(achievement)
        db.session.commit()

        flash(f'Conquista "{achievement.name}" criada!', 'success')
        return redirect(url_for('admin_achievements.list_achievements'))

    # Buscar modalidades para dropdown
    modalities = Modality.query.filter_by(is_active=True).all()

    return render_template('admin/achievements/form.html',
                           achievement=None,
                           criteria_types=CriteriaType,
                           modalities=modalities)


@achievements_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_achievement(id):
    """Editar conquista"""
    achievement = Achievement.query.get_or_404(id)

    if request.method == 'POST':
        # Atualizar icone se enviado
        if 'icon' in request.files:
            file = request.files['icon']
            if file.filename:
                try:
                    achievement.icon_url = save_achievement_icon(file)
                except ValueError as e:
                    flash(str(e), 'danger')
        elif request.form.get('icon_emoji'):
            achievement.icon_url = request.form['icon_emoji']

        criteria_extra = None
        if request.form['criteria_type'] == 'SPECIFIC_MODALITY':
            modality_id = request.form.get('modality_id')
            if modality_id:
                criteria_extra = {'modality_id': int(modality_id)}

        achievement.name = request.form['name']
        achievement.description = request.form.get('description')
        achievement.criteria_type = CriteriaType[request.form['criteria_type']]
        achievement.criteria_value = int(request.form['criteria_value'])
        achievement.criteria_extra = criteria_extra
        achievement.xp_reward = int(request.form.get('xp_reward', 0))
        achievement.color = request.form.get('color', '#FFD700')

        db.session.commit()

        flash(f'Conquista "{achievement.name}" atualizada!', 'success')
        return redirect(url_for('admin_achievements.list_achievements'))

    modalities = Modality.query.filter_by(is_active=True).all()

    return render_template('admin/achievements/form.html',
                           achievement=achievement,
                           criteria_types=CriteriaType,
                           modalities=modalities)


@achievements_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_achievement(id):
    """Desativar conquista"""
    achievement = Achievement.query.get_or_404(id)
    achievement.is_active = False
    db.session.commit()

    flash(f'Conquista "{achievement.name}" desativada.', 'info')
    return redirect(url_for('admin_achievements.list_achievements'))


@achievements_bp.route('/activate/<int:id>', methods=['POST'])
@login_required
@admin_required
def activate_achievement(id):
    """Reativar conquista"""
    achievement = Achievement.query.get_or_404(id)
    achievement.is_active = True
    db.session.commit()

    flash(f'Conquista "{achievement.name}" reativada.', 'success')
    return redirect(url_for('admin_achievements.list_achievements'))


@achievements_bp.route('/check-all', methods=['POST'])
@login_required
@admin_required
def check_all_achievements():
    """Verificar conquistas de todos os usuarios"""
    from app.services.achievement_checker import AchievementChecker

    total = AchievementChecker.check_all_users()

    return jsonify({'unlocked': total})


@achievements_bp.route('/<int:id>/unlocks')
@login_required
@admin_required
def get_unlocks(id):
    """Retornar lista de quem desbloqueou"""
    achievement = Achievement.query.get_or_404(id)

    unlocks = []
    for ua in achievement.unlocks:
        unlocks.append({
            'user_name': ua.user.name,
            'user_email': ua.user.email,
            'unlocked_at': ua.unlocked_at.strftime('%d/%m/%Y %H:%M'),
            'notified': ua.notified
        })

    return jsonify({'unlocks': unlocks})
