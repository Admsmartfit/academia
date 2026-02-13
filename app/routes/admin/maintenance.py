from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from app.routes.admin.dashboard import admin_required
from app.utils.backup import backup_database, list_backups, restore_database

maintenance_bp = Blueprint('admin_maintenance', __name__, url_prefix='/admin/maintenance')


@maintenance_bp.route('/')
@login_required
@admin_required
def index():
    """Painel de manutencao e backups"""
    backups = list_backups()
    return render_template('admin/maintenance/index.html', backups=backups)


@maintenance_bp.route('/backup/create', methods=['POST'])
@login_required
@admin_required
def create_backup():
    """Cria um novo backup do banco de dados"""
    success = backup_database()
    if success:
        return jsonify({'success': True, 'message': 'Backup criado com sucesso!'})
    return jsonify({'success': False, 'error': 'Erro ao criar backup.'}), 500


@maintenance_bp.route('/backup/restore', methods=['POST'])
@login_required
@admin_required
def restore_backup():
    """Restaura banco de dados a partir de um backup"""
    filename = request.json.get('filename')
    if not filename:
        return jsonify({'success': False, 'error': 'Nome do arquivo obrigatorio'}), 400

    try:
        restore_database(filename)
        return jsonify({'success': True, 'message': f'Banco restaurado de {filename}. Reinicie a aplicacao.'})
    except FileNotFoundError:
        return jsonify({'success': False, 'error': 'Arquivo de backup nao encontrado'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
