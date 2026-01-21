# app/services/image_handler.py

from werkzeug.utils import secure_filename
from PIL import Image
import os
import uuid
from flask import current_app


class ImageHandler:
    """
    Gerencia upload e processamento de imagens
    """

    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

    MAX_SIZE = {
        'package': (800, 600),
        'achievement': (200, 200),
        'payment': (1200, 1200),
    }

    @staticmethod
    def allowed_file(filename):
        """Verifica se extensao e permitida"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in ImageHandler.ALLOWED_EXTENSIONS

    @staticmethod
    def save_package_image(file):
        """
        Salva foto de pacote
        Retorna: nome do arquivo salvo
        """
        if not file or not ImageHandler.allowed_file(file.filename):
            raise ValueError("Arquivo de imagem invalido")

        # Gerar nome unico
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"

        # Caminho
        upload_folder = os.path.join(
            current_app.root_path,
            'static/uploads/packages'
        )
        os.makedirs(upload_folder, exist_ok=True)

        filepath = os.path.join(upload_folder, filename)

        # Redimensionar e salvar
        img = Image.open(file)
        img.thumbnail(ImageHandler.MAX_SIZE['package'], Image.Resampling.LANCZOS)
        img.save(filepath, optimize=True, quality=85)

        return filename

    @staticmethod
    def save_achievement_icon(file):
        """Salva icone de conquista"""
        if not file or not ImageHandler.allowed_file(file.filename):
            raise ValueError("Arquivo de imagem invalido")

        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"

        upload_folder = os.path.join(
            current_app.root_path,
            'static/uploads/achievements'
        )
        os.makedirs(upload_folder, exist_ok=True)

        filepath = os.path.join(upload_folder, filename)

        # Redimensionar para quadrado
        img = Image.open(file)
        img.thumbnail(ImageHandler.MAX_SIZE['achievement'], Image.Resampling.LANCZOS)

        # Centralizar em fundo quadrado
        size = ImageHandler.MAX_SIZE['achievement']
        new_img = Image.new('RGBA', size, (255, 255, 255, 0))

        # Converter para RGBA se necessario
        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        new_img.paste(img, ((size[0] - img.size[0]) // 2, (size[1] - img.size[1]) // 2))

        new_img.save(filepath, optimize=True, quality=90)

        return f"/static/uploads/achievements/{filename}"

    @staticmethod
    def save_payment_proof(file, user_id, payment_id):
        """Salva comprovante de pagamento"""
        if not file or not ImageHandler.allowed_file(file.filename):
            raise ValueError("Arquivo invalido")

        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"payment_{user_id}_{payment_id}_{uuid.uuid4().hex[:8]}.{ext}"

        upload_folder = os.path.join(
            current_app.root_path,
            'static/uploads/payments'
        )
        os.makedirs(upload_folder, exist_ok=True)

        filepath = os.path.join(upload_folder, filename)

        # Redimensionar se muito grande
        img = Image.open(file)
        if img.size[0] > 1200 or img.size[1] > 1200:
            img.thumbnail(ImageHandler.MAX_SIZE['payment'], Image.Resampling.LANCZOS)

        img.save(filepath, optimize=True, quality=85)

        return f"/static/uploads/payments/{filename}"


# Funcoes helper
def save_package_image(file):
    return ImageHandler.save_package_image(file)


def save_achievement_icon(file):
    return ImageHandler.save_achievement_icon(file)


def save_payment_proof(file, user_id, payment_id):
    return ImageHandler.save_payment_proof(file, user_id, payment_id)
