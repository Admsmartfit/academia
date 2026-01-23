# app/models/system_config.py

from app import db
from datetime import datetime


class SystemConfig(db.Model):
    """
    Configuracoes do sistema.
    Armazena configuracoes globais como taxa de conversao de creditos.
    """
    __tablename__ = 'system_config'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Configuracoes padrao
    DEFAULT_CONFIGS = {
        'credits_per_real': {
            'value': '1',
            'description': 'Quantidade de creditos por cada R$1,00'
        },
        'academy_name': {
            'value': 'Academia Fitness',
            'description': 'Nome da academia'
        },
        'academy_address': {
            'value': 'Rua da Academia, 123',
            'description': 'Endereco da academia'
        }
    }

    @classmethod
    def get(cls, key: str, default: str = None) -> str:
        """
        Busca valor de uma configuracao.

        Args:
            key: Chave da configuracao
            default: Valor padrao se nao encontrar

        Returns:
            Valor da configuracao ou default
        """
        config = cls.query.filter_by(key=key).first()
        if config:
            return config.value

        # Retornar valor padrao do dicionario se existir
        if key in cls.DEFAULT_CONFIGS:
            return cls.DEFAULT_CONFIGS[key]['value']

        return default

    @classmethod
    def get_float(cls, key: str, default: float = 0.0) -> float:
        """Busca configuracao como float"""
        value = cls.get(key)
        try:
            return float(value) if value else default
        except (ValueError, TypeError):
            return default

    @classmethod
    def get_int(cls, key: str, default: int = 0) -> int:
        """Busca configuracao como inteiro"""
        value = cls.get(key)
        try:
            return int(float(value)) if value else default
        except (ValueError, TypeError):
            return default

    @classmethod
    def set(cls, key: str, value: str, description: str = None) -> 'SystemConfig':
        """
        Define valor de uma configuracao.

        Args:
            key: Chave da configuracao
            value: Valor a ser salvo
            description: Descricao opcional

        Returns:
            Objeto SystemConfig atualizado/criado
        """
        config = cls.query.filter_by(key=key).first()

        if config:
            config.value = str(value)
            if description:
                config.description = description
        else:
            config = cls(
                key=key,
                value=str(value),
                description=description or cls.DEFAULT_CONFIGS.get(key, {}).get('description', '')
            )
            db.session.add(config)

        db.session.commit()
        return config

    @classmethod
    def get_all(cls) -> dict:
        """Retorna todas as configuracoes como dicionario"""
        configs = {}

        # Primeiro, adicionar defaults
        for key, data in cls.DEFAULT_CONFIGS.items():
            configs[key] = {
                'value': data['value'],
                'description': data['description']
            }

        # Sobrescrever com valores do banco
        for config in cls.query.all():
            configs[config.key] = {
                'value': config.value,
                'description': config.description
            }

        return configs

    @classmethod
    def initialize_defaults(cls):
        """Inicializa configuracoes padrao no banco se nao existirem"""
        for key, data in cls.DEFAULT_CONFIGS.items():
            if not cls.query.filter_by(key=key).first():
                config = cls(
                    key=key,
                    value=data['value'],
                    description=data['description']
                )
                db.session.add(config)

        db.session.commit()

    @classmethod
    def calculate_credits(cls, price: float) -> int:
        """
        Calcula quantidade de creditos baseado no preco.

        Args:
            price: Preco em reais

        Returns:
            Quantidade de creditos
        """
        credits_per_real = cls.get_float('credits_per_real', 1.0)
        return int(price * credits_per_real)

    def __repr__(self):
        return f'<SystemConfig {self.key}={self.value}>'
