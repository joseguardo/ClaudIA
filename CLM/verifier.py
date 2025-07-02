import re
import difflib
from typing import List, Dict, Union

# Campos que vamos a evaluar
EVENT_FIELDS = ["name", "description", "clause_reference", "deadline", "relative_to_notice"]

def normalize(text: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]", "", text.lower())

def fuzzy_score(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, normalize(a), normalize(b)).ratio()

def match_chunk(chunk_text: str, event: Dict, thresholds: Dict = None) -> Dict:
    """
    Evalúa si un chunk contiene citas relevantes del evento.
    Retorna: score, matched_fields
    """
    thresholds = thresholds or {
        "name": 0.7,
        "description": 0.7,
        "clause_reference": 0.85,
        "deadline": 0.8,
        "relative_to_notice": 0.7,
    }

    score = 0
    matched_fields = []

    for event in [event] if isinstance(event, list) else [event]:
        for field in EVENT_FIELDS:
            val = event.get(field)
            if not val:
                continue

            if field == "clause_reference":
                # Búsqueda exacta o regex
                pattern = re.escape(val)
                if re.search(pattern, chunk_text):
                    matched_fields.append(field)
                    score += 2  # le damos más peso

            else:
                ratio = fuzzy_score(val, chunk_text)
                if ratio >= thresholds[field]:
                    matched_fields.append(field)
                    score += 1

    return {
        "score": score,
        "matched_fields": matched_fields
    }

def verify_event_sources(events: Union[Dict, List[Dict]], context_chunks: List[Dict], top_k: int = 3) -> Union[Dict, List[Dict]]:
    """
    Enriquece uno o varios eventos con citas textuales si las hay, sin alterar el contenido original.
    """
    if isinstance(events, dict):
        events = [events]  # Forzar lista uniforme

    verified_events = []

    for event in events:
        matches = []

        for chunk in context_chunks:
            result = match_chunk(chunk["text"], event)
            if result["score"] > 0:
                matches.append({
                    "chunk_id": chunk["chunk_id"],
                    "text_snippet": chunk["text"][:300],
                    "match_fields": result["matched_fields"],
                    "score": result["score"]
                })

        # Agregar citas si hay, si no, lista vacía
        event["source_citations"] = sorted(matches, key=lambda x: x["score"], reverse=True)[:top_k]
        verified_events.append(event)

    return verified_events 
