# app/services/wger_service.py

"""
Wger API integration service for exercise catalog.
Fetches exercises from the open-source Wger API (wger.de).
"""

import requests
import logging
import random
import re
from app.models.training import Exercise, MuscleGroup, DifficultyLevel
from app import db

logger = logging.getLogger(__name__)

WGER_BASE_URL = 'https://wger.de/api/v2'
WGER_LANGUAGE_EN = 2

# Wger category -> local muscle_group mapping
CATEGORY_MAP = {
    8: MuscleGroup.ARMS,       # Biceps
    9: MuscleGroup.LEGS,       # Calves
    10: MuscleGroup.CHEST,     # Chest
    11: MuscleGroup.BACK,      # Back (Lats)
    12: MuscleGroup.SHOULDERS, # Shoulders
    13: MuscleGroup.ARMS,      # Triceps
    14: MuscleGroup.LEGS,      # Legs (Quads/Hamstrings/Glutes)
    15: MuscleGroup.CORE,      # Abs
}

# Cache de equipamentos (id -> nome)
_equipment_cache = {}


def _get_equipment_names():
    """Busca todos os equipamentos da API e cacheia."""
    global _equipment_cache
    if _equipment_cache:
        return _equipment_cache
    try:
        resp = requests.get(
            f'{WGER_BASE_URL}/equipment/',
            params={'format': 'json', 'limit': 100},
            timeout=10
        )
        resp.raise_for_status()
        for item in resp.json().get('results', []):
            _equipment_cache[item['id']] = item['name']
    except Exception as e:
        logger.warning(f'Erro ao buscar equipamentos: {e}')
    return _equipment_cache


def _fetch_all_images():
    """Busca TODAS as imagens de exercicios de uma vez (muito mais rapido)."""
    images = {}
    url = f'{WGER_BASE_URL}/exerciseimage/'
    params = {'format': 'json', 'limit': 100, 'is_main': 'True'}

    while url:
        try:
            resp = requests.get(url, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            for img in data.get('results', []):
                ex_id = img.get('exercise_base') or img.get('exercise')
                if ex_id and img.get('image') and ex_id not in images:
                    images[ex_id] = img['image']
            url = data.get('next')
            params = {}  # next URL already has params
        except Exception as e:
            logger.warning(f'Erro ao buscar imagens (batch): {e}')
            break

    logger.info(f'Carregadas {len(images)} imagens de exercicios')
    return images


def _fetch_all_videos():
    """Busca TODOS os videos de exercicios de uma vez."""
    videos = {}
    url = f'{WGER_BASE_URL}/video/'
    params = {'format': 'json', 'limit': 100}

    while url:
        try:
            resp = requests.get(url, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            for vid in data.get('results', []):
                ex_id = vid.get('exercise_base') or vid.get('exercise')
                if ex_id and vid.get('video') and ex_id not in videos:
                    videos[ex_id] = vid['video']
            url = data.get('next')
            params = {}
        except Exception as e:
            logger.warning(f'Erro ao buscar videos (batch): {e}')
            break

    logger.info(f'Carregados {len(videos)} videos de exercicios')
    return videos


def _clean_html(text):
    """Remove basic HTML tags from Wger descriptions."""
    if not text:
        return ''
    clean = re.sub(r'<[^>]+>', '', text)
    clean = clean.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&quot;', '"')
    return clean.strip()


def import_exercises_to_db(max_exercises=9999):
    """
    Importa exercicios da API Wger para o banco local.
    Busca em ingles, com imagens e videos.
    Pula duplicatas pelo nome.
    Retorna contagem de exercicios importados.
    """
    logger.info('Iniciando importacao de exercicios do Wger...')

    # 1) Pre-carregar equipamentos, imagens e videos em batch (muito mais rapido)
    equipment_map = _get_equipment_names()
    logger.info(f'Equipamentos carregados: {len(equipment_map)}')

    images_map = _fetch_all_images()
    videos_map = _fetch_all_videos()

    # 2) Nomes que ja existem no banco (evita queries repetidas)
    existing_names = set(
        name for (name,) in db.session.query(Exercise.name).all()
    )

    # 3) Buscar exercicios paginados
    difficulties = [DifficultyLevel.BEGINNER, DifficultyLevel.INTERMEDIATE, DifficultyLevel.ADVANCED]
    imported = 0
    offset = 0
    batch_size = 100

    while imported < max_exercises:
        try:
            resp = requests.get(
                f'{WGER_BASE_URL}/exercise/',
                params={
                    'language': WGER_LANGUAGE_EN,
                    'limit': batch_size,
                    'offset': offset,
                    'format': 'json',
                    'status': 2,
                },
                timeout=20
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.error(f'Wger API error na pagina offset={offset}: {e}')
            break

        results = data.get('results', [])
        if not results:
            break

        for item in results:
            if imported >= max_exercises:
                break

            name = (item.get('name') or '').strip()
            if not name or name in existing_names:
                continue

            cat_id = item.get('category')
            muscle = CATEGORY_MAP.get(cat_id, MuscleGroup.FULL_BODY)
            description = _clean_html(item.get('description', ''))

            # Resolver equipamentos: IDs -> nomes
            equip_ids = item.get('equipment', [])
            equip_names = [equipment_map.get(eid, '') for eid in equip_ids]
            equip_str = ', '.join(n for n in equip_names if n) or None

            # exercise_base para buscar imagem/video
            ex_base_id = item.get('exercise_base') or item.get('id')

            thumbnail = images_map.get(ex_base_id)
            video_url = videos_map.get(ex_base_id)

            exercise = Exercise(
                name=name,
                muscle_group=muscle,
                description=description[:500] if description else None,
                thumbnail_url=thumbnail,
                video_url=video_url,
                difficulty_level=random.choice(difficulties),
                is_active=True,
                equipment_needed=equip_str
            )
            db.session.add(exercise)
            existing_names.add(name)
            imported += 1

        # Commit por pagina
        db.session.commit()
        logger.info(f'Importados ate agora: {imported} (offset={offset})')

        if not data.get('next'):
            break

        offset += batch_size

    logger.info(f'Importacao concluida: {imported} exercicios do Wger')
    return imported
