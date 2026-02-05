from flask import Blueprint, render_template
from flask_login import login_required, current_user

crm_bp = Blueprint('crm', __name__, url_prefix='/admin/crm')

@crm_bp.route('/dashboard')
@login_required
def dashboard():
    """Dashboard de CRM e Retencao"""
    if not current_user.is_admin and current_user.role != 'manager':
         # Fallback se nao tiver pagina de erro especifica
        return "Acesso negado", 403
    return render_template('admin/crm/dashboard.html')
