import openai
import json
import os
from typing import List, Dict, Union
from jinja2 import Template

def load_prompt_template(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def format_context_chunks(chunks: List[Dict], max_len: int = 100000) -> str:
    """
    Formatea los chunks como texto plano para el prompt.
    Trunca si supera longitud total permitida.
    """
    formatted = ""
    total_len = 0
    for c in chunks:
        block = f"Chunk {c['chunk_id']} (Groups: {', '.join(c['groups'])}):\n{c['text']}\n\n"
        if total_len + len(block) > max_len:
            break
        formatted += block
        total_len += len(block)
    return formatted.strip()

def parse_llm_json_response(output_text: str) -> Union[Dict, List, str]:
    """
    Intenta parsear correctamente la respuesta del LLM, incluso si está envuelta en comillas dobles.
    """
    try:
        # Primer intento directo
        return json.loads(output_text.strip())
    except json.JSONDecodeError:
        try:
            # Segundo intento: deserializa cadena embebida
            inner = json.loads(output_text.strip())
            return json.loads(inner)
        except Exception as e2:
            return {
                "error": "Double decoding failed",
                "raw_response": output_text
            }


def generate_event(query: str, context_chunks: List[Dict], client, model="o4-mini-2025-04-16", prompt_path="prompts/generate_event_prompt.txt") -> Dict:
    """
    Genera un evento contractual estructurado a partir de contexto y una query legal.
    """
    prompt_template = load_prompt_template(prompt_path)
    context_text = format_context_chunks(context_chunks)

    # Preparar prompt final
    final_prompt = Template(prompt_template).render(
        context=context_text,
        query=query,
        notice_date="30 June 2023"
    )
    # Llamada al modelo
    response = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": "You are an EPC contract assistant that returns structured events."},
            {"role": "user", "content": final_prompt}
        ]
    )
    print(f"La respuesta del modelo es: {response.output_text}")
    # En generate_event()
    output_text = response.output_text.strip()
    event = parse_llm_json_response(output_text)

    # Si no es dict o lista tras todo esto, lo marcamos como error
    if not isinstance(event, (dict, list)):
        print("❌ No se pudo interpretar una estructura válida.")
        return {
            "error": "Final fallback: not a JSON object/list",
            "raw_response": output_text
        }

    return event
