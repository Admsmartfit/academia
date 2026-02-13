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
    Otimizado para velocidade: sem tradução loop e com filtro de oficiais.
    """
    def fetch_from_api(status_code=2):
        try:
            params = {
                'language': WGER_LANGUAGE_EN,
                'limit': 60,  # Busca mais para filtrar duplicatas
                'format': 'json',
                'status': status_code,
                'is_main': True # Apenas exercicios principais/oficiais
            }
            resp = requests.get(f'{WGER_BASE_URL}/exercise/', params=params, timeout=10)
            resp.raise_for_status()
            return resp.json().get('results', [])
        except Exception as e:
            logger.error(f"Erro na sub-busca API (status={status_code}): {e}")
            return []

    try:
        logger.info(f"Iniciando busca de preview (limite {limit} novos)...")
        results = fetch_from_api(status_code=2)
        
        # Fallback: Se nao encontrar oficiais, busca qualquer um
        if not results:
            logger.warning("Nenhum exercicio oficial encontrado. Tentando geral...")
            results = fetch_from_api(status_code=None)

        if not results:
            return []

        # Otimizacao: Set de nomes existentes para busca O(1)
        existing_names = {e.name.lower().strip() for e in Exercise.query.with_entities(Exercise.name).all()}
        
        preview_list = []
        for item in results:
            # Pega nome original se disponivel, senao name normal
            name_en = item.get('name_original') or item.get('name', '')
            name_en = name_en.strip()
            
            if not name_en:
                continue
            
            # Filtro de duplicatas (check simples contra o nome em ingles por enquanto)
            # A traducao real so ocorre na importacao para nao travar o preview
            if name_en.lower() in existing_names:
                continue
            
            cat_id = item.get('category')
            muscle_group = CATEGORY_MAP.get(cat_id, MuscleGroup.FULL_BODY)
            
            preview_list.append({
                'wger_id': item['id'],
                'name': name_en, # Exibe em Ingles no preview para performance
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
    Realiza tradução aqui, sob demanda.
    """
    imported_count = 0
    difficulties = [DifficultyLevel.BEGINNER, DifficultyLevel.INTERMEDIATE, DifficultyLevel.ADVANCED]
    
    # Cache rapido de equipamentos
    try:
        equipment_resp = requests.get(f'{WGER_BASE_URL}/equipment/', params={'format': 'json', 'limit': 100}, timeout=10)
        equipment_map = {item['id']: item['name'] for item in equipment_resp.json().get('results', [])} if equipment_resp.ok else {}
    except:
        equipment_map = {}

    for wger_id in exercise_ids:
        try:
            # 1. Busca dados do exercicio
            ex_resp = requests.get(f'{WGER_BASE_URL}/exercise/{wger_id}/', params={'format': 'json'}, timeout=10)
            if not ex_resp.ok: continue
            ex_data = ex_resp.json()
            
            # 2. Traducao (AQUI e seguro demorar um pouco mais)
            original_name = ex_data.get('name', '')
            name = translate_text(original_name)
            description = translate_text(_clean_html(ex_data.get('description', '')))
            
            # Check final de duplicidade apos traducao
            if Exercise.query.filter(Exercise.name.ilike(name)).first():
                logger.info(f"Pussando {name} (ja existe)")
                continue
                
            # 3. Busca imagem
            img_resp = requests.get(f'{WGER_BASE_URL}/exerciseimage/', params={'exercise': wger_id, 'format': 'json'}, timeout=10)
            thumbnail = None
            if img_resp.ok:
                img_results = img_resp.json().get('results', [])
                if img_results:
                    thumbnail = img_results[0].get('image')
                    
            # 4. Busca video
            vid_resp = requests.get(f'{WGER_BASE_URL}/video/', params={'exercise': wger_id, 'format': 'json'}, timeout=10)
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
