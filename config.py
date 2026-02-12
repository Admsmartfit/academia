import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-12345'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # No Windows, o SQLite precisa de 3 barras (relativo) ou 4 (absoluto)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///academia.db'

    # Session cookie security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = 'Lax'

    # Configurações da Academia
    ACADEMIA_NAME = "Academia"
    
    # MegaAPI (WhatsApp)
    MEGAAPI_TOKEN = os.environ.get('MEGAAPI_TOKEN')
    MEGAAPI_BASE_URL = os.environ.get('MEGAAPI_BASE_URL', 'https://api.megaapi.com.br/v1')

    # NuPay Configuration (Pagamentos PIX)
    NUPAY_BASE_URL = os.environ.get('NUPAY_BASE_URL', 'https://api.spinpay.com.br')
    NUPAY_MERCHANT_KEY = os.environ.get('NUPAY_MERCHANT_KEY')
    NUPAY_MERCHANT_TOKEN = os.environ.get('NUPAY_MERCHANT_TOKEN')
    NUPAY_WEBHOOK_SECRET = os.environ.get('NUPAY_WEBHOOK_SECRET')

    # Base URL for callbacks (usado em webhooks e redirecionamentos)
    BASE_URL = os.environ.get('BASE_URL', 'http://localhost:5000')

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
