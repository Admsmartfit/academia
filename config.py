import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-12345'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # No Windows, o SQLite precisa de 3 barras (relativo) ou 4 (absoluto)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///academia.db'
    
    # Configurações da Academia
    ACADEMIA_NAME = "Academia"
    
    # MegaAPI (WhatsApp)
    MEGAAPI_TOKEN = os.environ.get('MEGAAPI_TOKEN')
    MEGAAPI_BASE_URL = os.environ.get('MEGAAPI_BASE_URL', 'https://api.megaapi.com.br/v1')

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
