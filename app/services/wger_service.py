# app/services/wger_service.py

"""
Wger API integration service for exercise catalog.
Fetches exercises from the open-source Wger API (wger.readthedocs.io).
"""

import requests
import logging
import random
from app.models.training import Exercise, MuscleGroup, DifficultyLevel
from app import db

logger = logging.getLogger(__name__)

WGER_BASE_URL = 'https://wger.de/api/v2'
WGER_LANGUAGE_PT = 10  # Portuguese
WGER_LANGUAGE_EN = 2   # English fallback

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
            cat_id = item.get('category')
            muscle = CATEGORY_MAP.get(cat_id, MuscleGroup.FULL_BODY)
            
            exercises.append({
                'wger_id': item['id'],
                'name': item.get('name', '').strip(),
                'description': _clean_html(item.get('description', '')),
                'category_id': cat_id,
                'muscle_group': muscle,
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


def import_exercises_to_db(language='pt', max_exercises=50):
    """
    Import exercises from Wger into local Exercise model.
    Skips duplicates by name.
    Returns count of imported exercises.
    """
    imported = 0
    offset = 0
    batch_size = 20
    
    # Simple heuristic distribution for difficulty if not provided
    difficulties = [DifficultyLevel.BEGINNER, DifficultyLevel.INTERMEDIATE, DifficultyLevel.ADVANCED]

    while imported < max_exercises:
        result = fetch_exercises(language=language, limit=batch_size, offset=offset)
        
        # Stop if no more results or error
        if not result['exercises'] and not result.get('next'):
            break
            
        # Try English fallback if Portuguese has no results strictly on first call
        if not result['exercises'] and language == 'pt' and offset == 0:
            result = fetch_exercises(language='en', limit=batch_size, offset=offset)
            if not result['exercises']:
                break

        for ex_data in result['exercises']:
            if imported >= max_exercises:
                break

            # Skip if already exists
            existing = Exercise.query.filter_by(name=ex_data['name']).first()
            if existing:
                continue

            # Fetch thumbnail
            images = fetch_exercise_images(ex_data['wger_id'])
            thumbnail = images[0] if images else None
            
            # Randomly assign difficulty since Wger doesn't provide it easily
            # In a real app, this should be curated manually later
            difficulty = random.choice(difficulties)

            exercise = Exercise(
                name=ex_data['name'],
                muscle_group=ex_data['muscle_group'],
                description=ex_data.get('description', '')[:500], # Trucate if too long
                thumbnail_url=thumbnail,
                difficulty_level=difficulty,
                is_active=True,
                equipment_needed=", ".join([str(e) for e in ex_data['equipment']]) if ex_data['equipment'] else None
            )
            db.session.add(exercise)
            imported += 1

        db.session.commit()
        
        if not result.get('next'):
            break
            
        offset += batch_size

    logger.info(f'Imported {imported} exercises from Wger')
    return imported


def _clean_html(text):
    """Remove basic HTML tags from Wger descriptions."""
    if not text:
        return ''
    import re
    # Remove all HTML tags
    clean = re.sub(r'<[^>]+>', '', text)
    # Replace common HTML entities
    clean = clean.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&quot;', '"')
    return clean.strip()
