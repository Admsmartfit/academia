
import os
from app import create_app, db
from app.models.user import User

app = create_app(os.getenv('FLASK_CONFIG') or 'default')

def create_admin():
    with app.app_context():
        print("--- Criar/Atualizar Administrador ---")
        email = input("Email do administrador (padrao: admin@academia.com): ") or "admin@academia.com"
        
        user = User.query.filter_by(email=email).first()
        
        if user:
            print(f"Usuario {email} encontrado.")
        else:
            print(f"Criando novo usuario {email}.")
            user = User(
                name="Admin",
                email=email,
                phone="00000000000",
                role="admin"
            )
        
        password = input("Nova senha: ")
        if not password:
            print("Senha nao pode ser vazia.")
            return

        user.set_password(password)
        user.role = "admin" # Garante que e admin
        
        db.session.add(user)
        try:
            db.session.commit()
            print(f"\nSucesso! Usuario {email} atualizado/criado como administrador.")
        except Exception as e:
            print(f"Erro ao salvar: {e}")
            db.session.rollback()

if __name__ == '__main__':
    create_admin()
