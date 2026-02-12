# app/services/wger_service.py

"""
Wger API integration service for exercise catalog.
Fetches exercises from the open-source Wger API (wger.readthedocs.io).
"""

import requests
import logging

logger = logging.getLogger(__name__)

WGER_BASE_URL = 'https://wger.de/api/v2'
WGER_LANGUAGE_PT = 10  # Portuguese
WGER_LANGUAGE_EN = 2   # English fallback

# Wger category -> local muscle_group mapping
CATEGORY_MAP = {
    8: 'arms',       # Biceps
    9: 'legs',       # Calves
    10: 'chest',     # Chest
    11: 'back',      # Back (Lats)
    12: 'shoulders', # Shoulders
    13: 'arms',      # Triceps
    14: 'legs',      # Legs (Quads/Hamstrings/Glutes)
    15: 'core',      # Abs
}


def fetch_exercises(language='pt', limit=100, offset=0, category=None):
    """
    Fetch exercises from Wger API.
    Returns list of exercises with name, description, category, images.
    """
    lang_id = WGER_LANGUAGE_PT if language == 'pt' else WGER_LANGUAGE_EN

    params = {
        'language': lang_id,
        'limit': limit,
        'offset': offset,
        'format': 'json',
        'status': 2,  # Only approved exercises
    }
    if category:
        params['category'] = category

    try:
        resp = requests.get(f'{WGER_BASE_URL}/exercise/', params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        exercises = []
        for item in data.get('results', []):
            exercises.append({
                'wger_id': item['id'],
                'name': item.get('name', '').strip(),
                'description': _clean_html(item.get('description', '')),
                'category_id': item.get('category'),
                'muscle_group': CATEGORY_MAP.get(item.get('category'), 'full_body'),
                'equipment': [e for e in item.get('equipment', [])],
            })

        return {
            'exercises': [e for e in exercises if e['name']],
            'count': data.get('count', 0),
            'next': data.get('next'),
        }
    except requests.RequestException as e:
        logger.error(f'Wger API error: {e}')
        return {'exercises': [], 'count': 0, 'next': None, 'error': str(e)}


def fetch_exercise_images(exercise_id):
    """Fetch images for a specific exercise from Wger."""
    try:
        resp = requests.get(
            f'{WGER_BASE_URL}/exerciseimage/',
            params={'exercise': exercise_id, 'format': 'json', 'is_main': True},
            timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        images = [img['image'] for img in data.get('results', []) if img.get('image')]
        return images
    except requests.RequestException as e:
        logger.error(f'Wger image fetch error: {e}')
        return []


def fetch_categories():
    """Fetch exercise categories from Wger."""
    try:
        resp = requests.get(f'{WGER_BASE_URL}/exercisecategory/', params={'format': 'json'}, timeout=10)
        resp.raise_for_status()
        return resp.json().get('results', [])
    except requests.RequestException as e:
        logger.error(f'Wger categories error: {e}')
        return []


def import_exercises_to_db(language='pt', max_exercises=200):
    """
    Import exercises from Wger into local Exercise model.
    Skips duplicates by name.
    Returns count of imported exercises.
    """
    from app.models.training import Exercise, MuscleGroup
    from app import db

    imported = 0
    offset = 0
    batch_size = 50

    while offset < max_exercises:
        result = fetch_exercises(language=language, limit=batch_size, offset=offset)
        if not result['exercises']:
            # Try English fallback if Portuguese has no results
            if language == 'pt' and offset == 0:
                result = fetch_exercises(language='en', limit=batch_size, offset=offset)
            if not result['exercises']:
                break

        for ex_data in result['exercises']:
            # Skip if already exists
            existing = Exercise.query.filter_by(name=ex_data['name']).first()
            if existing:
                continue

            muscle_group_str = ex_data.get('muscle_group', 'full_body')
            try:
                muscle_group = MuscleGroup(muscle_group_str)
            except ValueError:
                muscle_group = MuscleGroup.FULL_BODY

            # Fetch thumbnail
            images = fetch_exercise_images(ex_data['wger_id'])
            thumbnail = images[0] if images else None

            exercise = Exercise(
                name=ex_data['name'],
                muscle_group=muscle_group,
                description=ex_data.get('description', ''),
                thumbnail_url=thumbnail,
                is_active=True,
            )
            db.session.add(exercise)
            imported += 1

        db.session.commit()
        offset += batch_size

        if not result.get('next'):
            break

    logger.info(f'Imported {imported} exercises from Wger')
    return imported


def _clean_html(text):
    """Remove basic HTML tags from Wger descriptions."""
    if not text:
        return ''
    import re
    clean = re.sub(r'<[^>]+>', '', text)
    clean = clean.replace('&nbsp;', ' ').replace('&amp;', '&')
    return clean.strip()
