# scripts/seed_data.py

import sys
import os

# Adiciona o diretório raiz ao path para importar a app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import Modality, Package, User, SystemConfig
from decimal import Decimal
from datetime import datetime

def seed():
    app = create_app()
    with app.app_context():
        print("Limpando banco de dados...")
        # Apenas para facilitar os testes, mas cuidado em produção
        # db.drop_all() 
        db.create_all()

        # Configurações do Sistema
        if not SystemConfig.query.filter_by(key='credits_per_real').first():
            db.session.add(SystemConfig(key='credits_per_real', value='1.0', description='Créditos por Real'))
            print("Config 'credits_per_real' adicionada.")

        # 1. Criar Modalidades
        modalities_data = [
            {
                "name": "Musculação",
                "description": "Treino de força e resistência com equipamentos de ponta.",
                "color": "#FF6B35",
                "icon": "🏋️‍♂️",
                "credits_cost": 1
            },
            {
                "name": "Yoga",
                "description": "Equilíbrio, flexibilidade e paz interior para o seu dia.",
                "color": "#4ECDC4",
                "icon": "🧘‍♀️",
                "credits_cost": 2
            },
            {
                "name": "Spinning",
                "description": "Alta queima calórica e energia bruta sobre duas rodas.",
                "color": "#FFD93D",
                "icon": "🚴‍♂️",
                "credits_cost": 2
            }
        ]

        for mod_data in modalities_data:
            if not Modality.query.filter_by(name=mod_data["name"]).first():
                mod = Modality(**mod_data)
                db.session.add(mod)
                print(f"Modalidade '{mod.name}' criada.")

        # 2. Criar Pacotes
        packages_data = [
            {
                "name": "Pacote Bronze",
                "description": "Ideal para quem está começando ou treina esporadicamente.",
                "credits": 30,
                "price": Decimal("300.00"),
                "installments": 1,
                "installment_price": Decimal("300.00"),
                "validity_days": 30,
                "color": "#CD7F32",
                "is_featured": False,
                "display_order": 3,
                "welcome_xp_bonus": 0
            },
            {
                "name": "Pacote Silver",
                "description": "O equilíbrio perfeito entre custo e benefício para o seu treino.",
                "credits": 60,
                "price": Decimal("540.00"),
                "installments": 3,
                "installment_price": Decimal("180.00"),
                "validity_days": 60,
                "color": "#C0C0C0",
                "is_featured": False,
                "display_order": 2,
                "welcome_xp_bonus": 100
            },
            {
                "name": "Pacote Gold",
                "description": "Acesso total e benefícios exclusivos. O plano dos campeões.",
                "credits": 120,
                "price": Decimal("960.00"),
                "installments": 6,
                "installment_price": Decimal("160.00"),
                "validity_days": 180,
                "color": "#FFD700",
                "is_featured": True,
                "display_order": 1,
                "welcome_xp_bonus": 250,
                "extra_benefits": ["Toalha grátis", "Avaliação física mensal", "Prioridade na agenda"]
            }
        ]

        for pkg_data in packages_data:
            if not Package.query.filter_by(name=pkg_data["name"]).first():
                pkg = Package(**pkg_data)
                db.session.add(pkg)
                print(f"Pacote '{pkg.name}' criado.")

        # 3. Criar Usuários
        # Admin
        if not User.query.filter_by(email='admin@academia.com').first():
            admin = User(
                name="Admin Academia",
                email="admin@academia.com",
                phone="5511999999999",
                role="admin",
                is_active=True
            )
            admin.set_password("admin123")
            db.session.add(admin)
            print("Usuário Admin criado.")

        # Estudantes para o Ranking
        students_data = [
            {"name": "Ana Silva", "email": "ana@test.com", "xp": 1250},
            {"name": "Bruno Costa", "email": "bruno@test.com", "xp": 980},
            {"name": "Carla Nunes", "email": "carla@test.com", "xp": 850},
            {"name": "Diego Souza", "email": "diego@test.com", "xp": 420},
            {"name": "Elena Pires", "email": "elena@test.com", "xp": 150}
        ]

        for std_data in students_data:
            if not User.query.filter_by(email=std_data["email"]).first():
                user = User(
                    name=std_data["name"],
                    email=std_data["email"],
                    phone="5511888888888",
                    cpf="123.456.789-00",
                    role="student",
                    xp=std_data["xp"],
                    level=(std_data["xp"] // 100) + 1,
                    is_active=True
                )
                user.set_password("aluno123")
                db.session.add(user)
                print(f"Estudante '{user.name}' criado com {user.xp} XP.")

        db.session.commit()
        print("\nSeed finalizado com sucesso!")

if __name__ == "__main__":
    seed()
