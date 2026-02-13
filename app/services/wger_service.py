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
from deep_translator import GoogleTranslator

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

def translate_text(text, source='en', target='pt'):
    """Translate text using deep_translator."""
    if not text:
        return ""
    try:
        return GoogleTranslator(source=source, target=target).translate(text)
    except Exception as e:
        logger.warning(f"Translation failed for '{text[:20]}...': {e}")
        return text

def _clean_html(text):
    """Remove basic HTML tags from Wger descriptions."""
    if not text:
        return ''
    clean = re.sub(r'<[^>]+>', '', text)
    clean = clean.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&quot;', '"')
    return clean.strip()

def get_api_exercises_preview(limit=30):
    """
    Busca dados basicos da API para preview.
    Busca uma quantidade maior da API para filtrar os ja existentes e retornar apenas novos.
    """
    def fetch_from_api(status_code=2):
        try:
            resp = requests.get(
                f'{WGER_BASE_URL}/exercise/',
                params={
                    'language': WGER_LANGUAGE_EN,
                    'limit': 60, # Busca mais para ter margem de filtro
                    'format': 'json',
                    'status': status_code,
                },
                timeout=20
            )
            resp.raise_for_status()
            return resp.json().get('results', [])
        except Exception as e:
            logger.error(f"Erro na sub-busca API (status={status_code}): {e}")
            return []

    try:
        logger.info(f"Iniciando busca de preview (limite {limit} novos)...")
        results = fetch_from_api(status_code=2)
        
        # Fallback se não encontrar nada com status=2 (Published)
        if not results:
            logger.warning("Nenhum exercicio 'Published' encontrado. Tentando sem filtro de status...")
            results = fetch_from_api(status_code=None)

        if not results:
            return []

        # Pega nomes ja existentes para filtrar
        existing_names = {e.name.lower().strip() for e in Exercise.query.all()}
        
        preview_list = []
        for item in results:
            name_en = item.get('name', '').strip()
            if not name_en:
                continue
            
            # Tradução rápida (ou retorno do original se falhar)
            try:
                translated_name = translate_text(name_en)
            except:
                translated_name = name_en
                
            # Filtro de duplicatas (case-insensitive)
            if translated_name.lower().strip() in existing_names:
                continue
            
            # Mapeia categoria
            cat_id = item.get('category')
            muscle_group = CATEGORY_MAP.get(cat_id, MuscleGroup.FULL_BODY)
            
            preview_list.append({
                'wger_id': item['id'],
                'name': translated_name,
                'muscle_group': muscle_group
            })
            
            if len(preview_list) >= limit:
                break
                
        logger.info(f"Encontrados {len(preview_list)} novos exercicios para preview.")
        return preview_list
    except Exception as e:
        logger.error(f'Erro geral ao buscar preview da API: {e}')
        return []

def import_selected_exercises(exercise_ids):
    """
    Busca detalhes completos de uma lista de IDs e salva no banco.
    """
    imported_count = 0
    difficulties = [DifficultyLevel.BEGINNER, DifficultyLevel.INTERMEDIATE, DifficultyLevel.ADVANCED]
    
    # Cache de equipamentos para evitar muitas requests
    equipment_resp = requests.get(f'{WGER_BASE_URL}/equipment/', params={'format': 'json', 'limit': 100})
    equipment_map = {item['id']: item['name'] for item in equipment_resp.json().get('results', [])} if equipment_resp.ok else {}

    for wger_id in exercise_ids:
        try:
            # 1. Busca dados base do exercicio
            ex_resp = requests.get(f'{WGER_BASE_URL}/exercise/{wger_id}/', params={'format': 'json'})
            if not ex_resp.ok: continue
            ex_data = ex_resp.json()
            
            # 2. Traduz nome e descricao
            name = translate_text(ex_data.get('name', ''))
            description = translate_text(_clean_html(ex_data.get('description', '')))
            
            # Pula se ja existir um com esse nome
            if Exercise.query.filter_by(name=name).first():
                continue
                
            # 3. Busca imagem
            img_resp = requests.get(f'{WGER_BASE_URL}/exerciseimage/', params={'exercise': wger_id, 'format': 'json'})
            thumbnail = None
            if img_resp.ok:
                img_results = img_resp.json().get('results', [])
                if img_results:
                    thumbnail = img_results[0].get('image')
                    
            # 4. Busca video
            vid_resp = requests.get(f'{WGER_BASE_URL}/video/', params={'exercise': wger_id, 'format': 'json'})
            video_url = None
            if vid_resp.ok:
                vid_results = vid_resp.json().get('results', [])
                if vid_results:
                    video_url = vid_results[0].get('video')
            
            # 5. Processa equipamentos
            equip_ids = ex_data.get('equipment', [])
            equipment_needed = ", ".join([equipment_map.get(eid, str(eid)) for eid in equip_ids]) if equip_ids else None
            
            # 6. Salva
            cat_id = ex_data.get('category')
            muscle_group = CATEGORY_MAP.get(cat_id, MuscleGroup.FULL_BODY)
            
            new_ex = Exercise(
                name=name,
                muscle_group=muscle_group,
                description=description[:500] if description else None,
                thumbnail_url=thumbnail,
                video_url=video_url,
                difficulty_level=random.choice(difficulties),
                is_active=True,
                equipment_needed=equipment_needed
            )
            db.session.add(new_ex)
            imported_count += 1
            
        except Exception as e:
            logger.error(f'Erro ao importar exercicio ID {wger_id}: {e}')
            continue
            
    db.session.commit()
    return imported_count
