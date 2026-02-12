# app/routes/marketing.py

from flask import Blueprint, render_template
from app.models import Package, Modality, User
from app import db
from sqlalchemy import func

marketing_bp = Blueprint('marketing', __name__)

def anonymize_name(name):
    """
    Retorna primeira letra + asteriscos + última letra.
    Ex: "Ana Silva" -> "A*****a"
    """
    if not name:
        return ""
    name = name.strip()
    if len(name) <= 2:
        return name[0] + "*" * (len(name)-1)
    return name[0] + "*" * 5 + name[-1]

@marketing_bp.route('/')
def index():
    # Busca packages ativos ordenados por display_order
    packages = Package.query.filter_by(is_active=True).order_by(Package.display_order).all()
    
    # Busca modalities ativas
    modalities = Modality.query.filter_by(is_active=True).all()
    
    # Busca top 10 users por XP (para hall da fama)
    top_users = User.query.filter_by(role='student', is_active=True)\
        .order_by(User.xp.desc()).limit(10).all()
    
    # Calcula total de XP de todos os alunos
    total_xp = db.session.query(func.sum(User.xp)).filter(User.role == 'student').scalar() or 0
    
    # Converte packages para dict para o simulador (JS)
    packages_json = []
    for p in packages:
        packages_json.append({
            'id': p.id,
            'name': p.name,
            'credits': p.credits,
            'price': float(p.price),
            'installments': p.installments,
            'installment_price': float(p.installment_price) if p.installment_price else 0,
            'extra_benefits': p.extra_benefits or [],
            'badge': p.badge,
            'is_featured': p.is_featured
        })
    
    return render_template(
        'marketing/index.html',
        packages=packages,
        packages_json=packages_json,
        modalities=modalities,
        top_users=top_users,
        total_xp=total_xp,
        anonymize_name=anonymize_name
    )


@marketing_bp.route('/offline')
def offline():
    return render_template('offline.html')
