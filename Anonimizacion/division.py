from typing import List, Dict, Any, Union
import re
import json


def split_into_paragraphs(text: str) -> List[str]:
    """
    Divide el texto en párrafos basándose en líneas en blanco.
    """
    # Eliminar espacios en blanco al inicio y al final
    text = text.strip()
    
    # Dividir por líneas en blanco (uno o más saltos de línea)
    paragraphs = re.split(r'\n\s*\n', text)
    
    # Filtrar párrafos vacíos
    paragraphs = [p.strip() for p in paragraphs if p.strip()]
    
    return paragraphs

def create_chunks(paragraphs: List[str], chunk_size: int) -> List[str]:
    """
    Agrupa los párrafos en chunks del tamaño especificado.
    """
    chunks = []
    for i in range(0, len(paragraphs), chunk_size):
        chunk = '\n\n'.join(paragraphs[i:i+chunk_size])
        chunks.append(chunk)
    return chunks

def create_empty_result_template_fase1() -> Dict[str, List[str]]:
    """
    Crea una estructura de resultado vacía con las claves para la primera fase (datos personales).
    """
    return {
        "Nombres": [],
        "Apellidos": [],
        "DNI": [],
        "NIE": [],
        "Pasaporte": [],
        "Numero_telefonico": [],
        "IBAN": [],
        "Emails": [],
        "Identificador_fiscal": [],
        "Otros_Identificadores_Numericos": []
    }

def create_empty_result_template_fase2() -> Dict[str, List[str]]:
    """
    Crea una estructura de resultado vacía con las claves para la segunda fase (datos contextuales).
    """
    return {
        "Referencia_catastral": [],
        "Fechas": [],
        "Valores_monetarios": [],
        "Regiones": [],
        "Nombres_Empresas": [],
        "Paises": [],
        "Ciudades": [],
        "Direcciones": [],
        "Porcentajes": [],
        "Cuantias_en_palabras": [], 
        "Codigos_postales": [],
        "Numero_participaciones": [], 
        "Hojas_registrales": [],
        "Otros": []
    }

def create_empty_result_template_combined() -> Dict[str, List[str]]:
    """
    Crea una estructura de resultado vacía con todas las claves de ambas fases.
    """
    template_fase1 = create_empty_result_template_fase1()
    template_fase2 = create_empty_result_template_fase2()
    
    # Combinar ambos templates
    combined_template = {}
    combined_template.update(template_fase1)
    combined_template.update(template_fase2)
    
    return combined_template