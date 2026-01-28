import os
import uuid
from flask import current_app
from werkzeug.utils import secure_filename

class HealthHandler:
    """
    Gerencia upload de atestados médicos
    """
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB

    @staticmethod
    def allowed_file(filename):
        """Verifica se extensão é permitida"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in HealthHandler.ALLOWED_EXTENSIONS

    @staticmethod
    def save_certificate(file, user_id):
        """
        Salva atestado médico de um usuário
        Retorna: URL do arquivo salvo
        """
        if not file or not HealthHandler.allowed_file(file.filename):
            raise ValueError("Arquivo inválido. Use PDF, JPG ou PNG.")

        # Verificar tamanho (embora o Flask geralmente limite via MAX_CONTENT_LENGTH)
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0)
        
        if size > HealthHandler.MAX_CONTENT_LENGTH:
            raise ValueError("Arquivo muito grande. O limite é 5MB.")

        # Gerar nome único e seguro
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"certificate_{user_id}_{uuid.uuid4().hex[:8]}.{ext}"
        
        upload_folder = os.path.join(
            current_app.root_path,
            'static/uploads/health'
        )
        os.makedirs(upload_folder, exist_ok=True)
        
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)
        
        return f"/static/uploads/health/{filename}"
