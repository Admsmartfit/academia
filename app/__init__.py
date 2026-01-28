# app/__init__.py

import os
from datetime import datetime, timedelta
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import config

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()


def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Inicializar extensoes
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # Configurar login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Faca login para acessar esta pagina.'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        return User.query.get(int(user_id))

    # Context processor para templates
    @app.context_processor
    def utility_processor():
        return {
            'now': datetime.now,
            'timedelta': timedelta
        }

    # Registrar blueprints
    from app.routes.marketing import marketing_bp
    from app.routes.auth import auth_bp
    from app.routes.student import student_bp
    from app.routes.shop import shop_bp
    from app.routes.admin.dashboard import admin_bp
    from app.routes.admin.packages import packages_bp
    from app.routes.admin.modalities import modalities_bp
    from app.routes.admin.schedules import schedules_bp
    from app.routes.admin.payments import payments_bp
    from app.routes.admin.achievements import achievements_bp
    from app.routes.admin.whatsapp import whatsapp_bp
    from app.routes.admin.users import users_bp
    from app.routes.admin.megaapi_config import megaapi_config_bp
    from app.routes.admin.nupay_config import nupay_config_bp
    from app.routes.admin.settings import settings_bp
    from app.routes.admin.conversion_rules import conversion_rules_bp
    from app.routes.instructor import instructor_bp
    from app.routes.webhooks import webhooks_bp
    from app.routes.health import health_bp
    from app.routes.admin.health import admin_health_bp

    app.register_blueprint(marketing_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(shop_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(packages_bp)
    app.register_blueprint(modalities_bp)
    app.register_blueprint(schedules_bp)
    app.register_blueprint(payments_bp)
    app.register_blueprint(achievements_bp)
    app.register_blueprint(whatsapp_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(megaapi_config_bp)
    app.register_blueprint(nupay_config_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(conversion_rules_bp)
    app.register_blueprint(instructor_bp)
    app.register_blueprint(webhooks_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(admin_health_bp)

    # Iniciar scheduler
    if not app.debug or os.getenv('WERKZEUG_RUN_MAIN') == 'true':
        from app.utils.scheduler import init_scheduler
        init_scheduler(app)

    # Registrar comandos CLI
    from app.cli import register_cli_commands
    register_cli_commands(app)

    return app
