# app/models/user.py

from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import enum
import re


class UserRole(enum.Enum):
    ADMIN = "admin"
    STUDENT = "student"
    INSTRUCTOR = "instructor"


class Gender(enum.Enum):
    MALE = "male"
    FEMALE = "female"


class User(UserMixin, db.Model):
    """
    Modelo de usuario do sistema
    """
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    # CPF (necessário para NuPay)
    cpf = db.Column(db.String(14), nullable=True)  # Formato: 123.456.789-00

    # Sexo (necessário para modalidades com segregação)
    gender = db.Column(db.Enum(Gender), nullable=True)

    # Role
    role = db.Column(db.String(20), default='student')

    # Gamificacao
    xp = db.Column(db.Integer, default=0)  # XP total historico (para ranking)
    level = db.Column(db.Integer, default=1)

    # Cache de XP e Creditos (atualizados por triggers/services)
    xp_available = db.Column(db.Integer, default=0)  # XP disponivel para conversao (janela 3 meses)
    credits_balance = db.Column(db.Integer, default=0)  # Total de creditos ativos (wallets)

    # Reconhecimento Facial
    face_encoding = db.Column(db.LargeBinary, nullable=True)
    face_encoding_version = db.Column(db.String(10), default='v1')
    face_registered_at = db.Column(db.DateTime, nullable=True)
    face_last_recognized = db.Column(db.DateTime, nullable=True)
    face_confidence_threshold = db.Column(db.Float, default=0.6)

    # Perfil
    photo_url = db.Column(db.String(255))

    # Status
    is_active = db.Column(db.Boolean, default=True)

    # Datas
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    def set_password(self, password):
        """Define a senha do usuario"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verifica a senha do usuario"""
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_student(self):
        return self.role == 'student'

    @property
    def is_instructor(self):
        return self.role == 'instructor'

    @property
    def is_male(self):
        return self.gender == Gender.MALE

    @property
    def is_female(self):
        return self.gender == Gender.FEMALE

    @property
    def gender_label(self):
        if self.gender == Gender.MALE:
            return 'Masculino'
        elif self.gender == Gender.FEMALE:
            return 'Feminino'
        return 'Não informado'

    @property
    def active_subscription(self):
        """Retorna a assinatura ativa do usuario"""
        from app.models.subscription import Subscription, SubscriptionStatus
        return Subscription.query.filter_by(
            user_id=self.id,
            status=SubscriptionStatus.ACTIVE
        ).first()

    @property
    def total_credits(self):
        """Total de creditos disponiveis"""
        from app.models.subscription import Subscription, SubscriptionStatus
        subscriptions = Subscription.query.filter_by(
            user_id=self.id,
            status=SubscriptionStatus.ACTIVE
        ).all()
        return sum(s.credits_remaining for s in subscriptions)

    @property
    def completed_bookings_count(self):
        """Total de aulas completadas"""
        from app.models.booking import Booking, BookingStatus
        return Booking.query.filter_by(
            user_id=self.id,
            status=BookingStatus.COMPLETED
        ).count()

    def add_xp(self, amount, source_type=None, source_id=None, description=None):
        """
        Adiciona XP ao usuario.
        Cria entrada no XPLedger para rastreamento granular.
        """
        from app.models.xp_ledger import XPLedger, XPSourceType

        # Atualiza XP total (para ranking)
        self.xp += amount

        # Calcula novo nivel (cada 100 XP = 1 nivel)
        new_level = (self.xp // 100) + 1
        if new_level > self.level:
            self.level = new_level

        # Cria entrada no ledger para rastreamento
        if source_type is None:
            source_type = XPSourceType.BONUS

        XPLedger.create_entry(
            user_id=self.id,
            xp_amount=amount,
            source_type=source_type,
            source_id=source_id,
            description=description
        )

        # Atualiza cache de XP disponivel
        self.refresh_xp_cache()

        db.session.commit()

    def refresh_xp_cache(self):
        """Atualiza cache de XP disponivel para conversao"""
        from app.models.xp_ledger import XPLedger
        self.xp_available = XPLedger.get_user_available_xp(self.id)

    def refresh_credits_cache(self):
        """Atualiza cache de creditos totais"""
        from app.models.credit_wallet import CreditWallet
        self.credits_balance = CreditWallet.get_user_total_credits(self.id)

    def refresh_all_caches(self):
        """Atualiza todos os caches do usuario"""
        self.refresh_xp_cache()
        self.refresh_credits_cache()
        db.session.commit()

    @property
    def wallet_credits(self):
        """Total de creditos em wallets ativas (com FIFO)"""
        from app.models.credit_wallet import CreditWallet
        return CreditWallet.get_user_total_credits(self.id)

    @property
    def expiring_credits(self):
        """Creditos que vao expirar em 7 dias"""
        from app.models.credit_wallet import CreditWallet
        wallets = CreditWallet.get_expiring_soon(self.id, days=7)
        return sum(w.credits_remaining for w in wallets)

    @staticmethod
    def validate_cpf(cpf):
        """
        Valida CPF usando algoritmo oficial dos dígitos verificadores.
        Retorna True se válido, False se inválido.
        """
        if not cpf:
            return False

        # Remove caracteres não numéricos
        cpf = re.sub(r'[^0-9]', '', cpf)

        # Verifica se tem 11 dígitos
        if len(cpf) != 11:
            return False

        # Verifica se todos os dígitos são iguais (ex: 111.111.111-11)
        if cpf == cpf[0] * 11:
            return False

        # Calcula primeiro dígito verificador
        soma = 0
        for i in range(9):
            soma += int(cpf[i]) * (10 - i)
        resto = soma % 11
        digito1 = 0 if resto < 2 else 11 - resto

        if int(cpf[9]) != digito1:
            return False

        # Calcula segundo dígito verificador
        soma = 0
        for i in range(10):
            soma += int(cpf[i]) * (11 - i)
        resto = soma % 11
        digito2 = 0 if resto < 2 else 11 - resto

        if int(cpf[10]) != digito2:
            return False

        return True

    @staticmethod
    def format_cpf(cpf):
        """
        Formata CPF para o padrão XXX.XXX.XXX-XX.
        Retorna None se CPF inválido.
        """
        if not cpf:
            return None

        # Remove caracteres não numéricos
        cpf = re.sub(r'[^0-9]', '', cpf)

        if len(cpf) != 11:
            return None

        return f'{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}'

    def has_valid_screening(self, screening_type):
        """Verifica se usuário tem screening válido"""
        from app.models.health import HealthScreening, ScreeningStatus
        latest = HealthScreening.query.filter_by(
            user_id=self.id,
            screening_type=screening_type,
            status=ScreeningStatus.APTO
        ).filter(
            HealthScreening.expires_at > datetime.utcnow()
        ).order_by(HealthScreening.created_at.desc()).first()

        return latest is not None

    def can_access_modality(self, modality):
        """Verifica se pode acessar uma modalidade específica"""
        from app.models.health import ScreeningType
        # PAR-Q obrigatório para todos
        if not self.has_valid_screening(ScreeningType.PARQ):
            return False, "Preencha o questionário de saúde (PAR-Q)"

        # Se for FES, precisa também de anamnese EMS
        if modality.name == "Eletroestimulacao FES":
            if not self.has_valid_screening(ScreeningType.EMS):
                return False, "Preencha a anamnese de eletroestimulação"

        return True, "OK"

    def get_screening_status(self, screening_type):
        """Retorna status do screening"""
        from app.models.health import HealthScreening, ScreeningStatus
        latest = HealthScreening.query.filter_by(
            user_id=self.id,
            screening_type=screening_type
        ).order_by(HealthScreening.created_at.desc()).first()

        if not latest:
            return None

        if latest.expires_at < datetime.utcnow():
            return ScreeningStatus.EXPIRADO

        return latest.status

    def __repr__(self):
        return f'<User {self.name}>'
