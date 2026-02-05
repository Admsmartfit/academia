# app/services/face_service.py

from __future__ import annotations

import logging
import io
import base64
from typing import Optional, Dict, List, Tuple
from datetime import datetime

try:
    import numpy as np
    from PIL import Image
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    np = None
    Image = None
    face_recognition = None
    FACE_RECOGNITION_AVAILABLE = False

from app import db
from app.models.user import User
from app.models.face_recognition import FaceRecognitionLog

logger = logging.getLogger(__name__)


class FaceRecognitionService:
    """
    Servico para reconhecimento facial usando face_recognition (dlib).

    Baseado no modelo ResNet-34 treinado no dataset LFW com 99.38% de acuracia.
    """

    def __init__(self, tolerance: float = 0.6):
        """
        Args:
            tolerance: Limite de distancia para match (padrao: 0.6)
                      Valores menores = mais rigoroso
                      Valores maiores = mais permissivo
        """
        self.tolerance = tolerance

    def enroll_face(self, user_id: int, image_data) -> Dict:
        """
        Registra a face de um usuario no sistema.

        Args:
            user_id: ID do usuario
            image_data: Bytes da imagem ou base64 string

        Returns:
            dict com success, message, confidence, encoding_size
        """
        if not FACE_RECOGNITION_AVAILABLE:
            return {
                'success': False,
                'message': 'Biblioteca face_recognition nao instalada',
                'confidence': 0,
                'encoding_size': 0
            }

        user = User.query.get(user_id)
        if not user:
            return {
                'success': False,
                'message': 'Usuario nao encontrado',
                'confidence': 0,
                'encoding_size': 0
            }

        try:
            # Converter para numpy array
            image_array = self._image_to_array(image_data)

            # Validar qualidade
            quality = self.validate_image_quality(image_data)
            if not quality['valid']:
                return {
                    'success': False,
                    'message': 'Qualidade da imagem insuficiente: ' + ', '.join(quality['issues']),
                    'confidence': 0,
                    'encoding_size': 0
                }

            # Detectar faces
            face_locations = face_recognition.face_locations(image_array, model='hog')

            if len(face_locations) == 0:
                logger.warning(f"Enrollment: nenhuma face detectada para user {user_id}")
                return {
                    'success': False,
                    'message': 'Nenhuma face detectada na imagem. Tente novamente com melhor iluminacao.',
                    'confidence': 0,
                    'encoding_size': 0
                }

            if len(face_locations) > 1:
                logger.warning(f"Enrollment: {len(face_locations)} faces detectadas para user {user_id}")
                return {
                    'success': False,
                    'message': f'Foram detectadas {len(face_locations)} faces. A imagem deve conter apenas uma face.',
                    'confidence': 0,
                    'encoding_size': 0
                }

            # Extrair encoding (128 dimensoes)
            encodings = face_recognition.face_encodings(image_array, face_locations, model='large')

            if len(encodings) == 0:
                return {
                    'success': False,
                    'message': 'Nao foi possivel extrair caracteristicas da face. Tente outra foto.',
                    'confidence': 0,
                    'encoding_size': 0
                }

            encoding = encodings[0]

            # Salvar encoding no usuario
            user.face_encoding = self._encoding_to_bytes(encoding)
            user.face_encoding_version = 'v1'
            user.face_registered_at = datetime.utcnow()

            db.session.commit()

            confidence = 100.0  # Enrollment sempre tem confianca maxima
            logger.info(f"Face registrada com sucesso para user {user_id}")

            return {
                'success': True,
                'message': 'Face cadastrada com sucesso!',
                'confidence': confidence,
                'encoding_size': len(encoding)
            }

        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro no enrollment para user {user_id}: {str(e)}")
            return {
                'success': False,
                'message': f'Erro ao processar imagem: {str(e)}',
                'confidence': 0,
                'encoding_size': 0
            }

    def recognize_face(self, image_data, ip_address: str = None,
                       user_agent: str = None) -> Optional[Dict]:
        """
        Reconhece uma face e retorna o usuario correspondente.

        Args:
            image_data: Bytes da imagem ou base64 string
            ip_address: IP do cliente (para log)
            user_agent: User-Agent do cliente (para log)

        Returns:
            dict com user_id, user, confidence, distance ou None
        """
        if not FACE_RECOGNITION_AVAILABLE:
            logger.error("face_recognition nao disponivel")
            return None

        try:
            # Extrair encoding da imagem recebida
            image_array = self._image_to_array(image_data)
            face_locations = face_recognition.face_locations(image_array, model='hog')

            if len(face_locations) == 0:
                self._log_attempt(
                    user_id=None, confidence=0, success=False,
                    ip_address=ip_address, user_agent=user_agent,
                    error='Nenhuma face detectada'
                )
                return None

            # Usar a primeira face detectada
            encodings = face_recognition.face_encodings(image_array, face_locations[:1], model='large')
            if len(encodings) == 0:
                self._log_attempt(
                    user_id=None, confidence=0, success=False,
                    ip_address=ip_address, user_agent=user_agent,
                    error='Encoding falhou'
                )
                return None

            unknown_encoding = encodings[0]

            # Buscar todos os usuarios com face cadastrada
            users_with_face = User.query.filter(
                User.face_encoding.isnot(None),
                User.is_active == True
            ).all()

            if not users_with_face:
                self._log_attempt(
                    user_id=None, confidence=0, success=False,
                    ip_address=ip_address, user_agent=user_agent,
                    error='Nenhum usuario com face cadastrada'
                )
                return None

            # Comparar com todos os encodings cadastrados
            known_encodings = []
            known_users = []
            for user in users_with_face:
                try:
                    enc = self._bytes_to_encoding(user.face_encoding)
                    known_encodings.append(enc)
                    known_users.append(user)
                except Exception as e:
                    logger.warning(f"Encoding invalido para user {user.id}: {e}")
                    continue

            if not known_encodings:
                return None

            # Calcular distancias
            distances = face_recognition.face_distance(known_encodings, unknown_encoding)

            # Encontrar menor distancia
            min_idx = np.argmin(distances)
            min_distance = distances[min_idx]
            best_user = known_users[min_idx]

            # Usar threshold do usuario ou padrao
            threshold = best_user.face_confidence_threshold or self.tolerance

            if min_distance <= threshold:
                confidence = (1 - min_distance) * 100

                # Atualizar ultimo reconhecimento
                best_user.face_last_recognized = datetime.utcnow()
                db.session.commit()

                # Log de sucesso
                self._log_attempt(
                    user_id=best_user.id, confidence=confidence,
                    success=True, ip_address=ip_address,
                    user_agent=user_agent
                )

                logger.info(f"Face reconhecida: user {best_user.id} ({best_user.name}) "
                           f"confianca={confidence:.1f}%")

                return {
                    'user_id': best_user.id,
                    'user': best_user,
                    'confidence': confidence,
                    'distance': float(min_distance)
                }
            else:
                # Nenhum match suficientemente proximo
                self._log_attempt(
                    user_id=None, confidence=(1 - min_distance) * 100,
                    success=False, ip_address=ip_address,
                    user_agent=user_agent,
                    error=f'Melhor match: distancia {min_distance:.3f} > threshold {threshold}'
                )
                return None

        except Exception as e:
            logger.error(f"Erro no reconhecimento: {str(e)}")
            self._log_attempt(
                user_id=None, confidence=0, success=False,
                ip_address=ip_address, user_agent=user_agent,
                error=str(e)
            )
            return None

    def validate_image_quality(self, image_data) -> Dict:
        """
        Valida qualidade da imagem antes de processar.

        Returns:
            dict com valid, issues, resolution
        """
        issues = []

        try:
            # Converter para PIL Image
            if isinstance(image_data, str):
                # Base64
                if ',' in image_data:
                    image_data = image_data.split(',')[1]
                img_bytes = base64.b64decode(image_data)
            elif isinstance(image_data, bytes):
                img_bytes = image_data
            else:
                return {'valid': False, 'issues': ['Formato de imagem invalido'], 'resolution': (0, 0)}

            img = Image.open(io.BytesIO(img_bytes))
            width, height = img.size

            # Resolucao minima
            if width < 640 or height < 480:
                # Aceitar mas avisar para resolucoes menores (320x240 de webcam)
                if width < 320 or height < 240:
                    issues.append(f'Resolucao muito baixa ({width}x{height}). Minimo: 320x240')

            # Tamanho maximo (5MB)
            if len(img_bytes) > 5 * 1024 * 1024:
                issues.append('Imagem muito grande. Maximo: 5MB')

            # Verificar modo de cor
            if img.mode not in ('RGB', 'RGBA', 'L'):
                issues.append(f'Modo de cor nao suportado: {img.mode}')

            return {
                'valid': len(issues) == 0,
                'issues': issues,
                'resolution': (width, height)
            }

        except Exception as e:
            return {
                'valid': False,
                'issues': [f'Erro ao processar imagem: {str(e)}'],
                'resolution': (0, 0)
            }

    def remove_face(self, user_id: int) -> Dict:
        """
        Remove face encoding do usuario (LGPD compliance).

        Args:
            user_id: ID do usuario

        Returns:
            dict com success e message
        """
        user = User.query.get(user_id)
        if not user:
            return {'success': False, 'message': 'Usuario nao encontrado'}

        if not user.face_encoding:
            return {'success': False, 'message': 'Usuario nao possui face cadastrada'}

        user.face_encoding = None
        user.face_encoding_version = None
        user.face_registered_at = None
        user.face_last_recognized = None

        db.session.commit()
        logger.info(f"Face removida para user {user_id} (LGPD)")

        return {
            'success': True,
            'message': 'Dados biometricos removidos com sucesso'
        }

    def get_face_status(self, user_id: int) -> Dict:
        """
        Retorna status do cadastro facial de um usuario.
        """
        user = User.query.get(user_id)
        if not user:
            return {
                'has_face': False,
                'registered_at': None,
                'last_recognized': None,
                'total_recognitions': 0
            }

        total = FaceRecognitionLog.query.filter_by(
            user_id=user_id,
            success=True
        ).count()

        return {
            'has_face': user.face_encoding is not None,
            'registered_at': user.face_registered_at.isoformat() if user.face_registered_at else None,
            'last_recognized': user.face_last_recognized.isoformat() if user.face_last_recognized else None,
            'total_recognitions': total
        }

    def _log_attempt(self, user_id, confidence, success,
                     ip_address=None, user_agent=None, error=None):
        """Registra tentativa de reconhecimento no log."""
        try:
            log = FaceRecognitionLog(
                user_id=user_id,
                confidence_score=confidence,
                success=success,
                ip_address=ip_address,
                user_agent=user_agent,
                error_message=error
            )
            db.session.add(log)
            db.session.commit()
        except Exception as e:
            logger.error(f"Erro ao salvar log de reconhecimento: {e}")
            db.session.rollback()

    @staticmethod
    def _image_to_array(image_data) -> np.ndarray:
        """
        Converte bytes ou base64 para numpy array.

        Suporta:
        - Bytes diretos
        - Base64 string
        - Base64 com prefixo data:image/...
        """
        if isinstance(image_data, str):
            # Remover prefixo data:image/...;base64,
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            img_bytes = base64.b64decode(image_data)
        elif isinstance(image_data, bytes):
            img_bytes = image_data
        else:
            raise TypeError(f"Formato de imagem nao suportado: {type(image_data)}")

        # Converter para PIL e depois para numpy
        img = Image.open(io.BytesIO(img_bytes))

        # Converter para RGB se necessario
        if img.mode == 'RGBA':
            img = img.convert('RGB')
        elif img.mode == 'L':
            img = img.convert('RGB')
        elif img.mode != 'RGB':
            img = img.convert('RGB')

        return np.array(img)

    @staticmethod
    def _encoding_to_bytes(encoding: np.ndarray) -> bytes:
        """Serializa numpy array para bytes."""
        return encoding.tobytes()

    @staticmethod
    def _bytes_to_encoding(data: bytes) -> np.ndarray:
        """Desserializa bytes para numpy array (128 floats)."""
        return np.frombuffer(data, dtype=np.float64)
