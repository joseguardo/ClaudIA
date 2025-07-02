import json
import boto3
import re
import concurrent.futures
from typing import List, Dict, Any, Union, Tuple
from jinja2 import Template
from formateo_call import formateo_call_datos_personales, formateo_call_datos_contextuales
from division import (
    split_into_paragraphs, 
    create_chunks, 
    create_empty_result_template_fase1, 
    create_empty_result_template_fase2,
    create_empty_result_template_combined
)

bedrock_runtime = boto3.client('bedrock-runtime', region_name='eu-central-1')
CHUNK_SIZE = 25  # Número de párrafos por chunk
MAX_WORKERS = 15  # Número máximo de hilos concurrentes
def lambda_handler(event, context):
    """
    Manejador principal de la función Lambda que dirige las peticiones según el tipo de función solicitada.
    """
    try:
        # Obtener el cuerpo de la petición - puede venir ya como un diccionario o como string
        body_str = event.get('body', '')
        
        # Si body_str está vacío
        if not body_str:
            return {
                'statusCode': 400,
                'body': json.dumps('Error: Empty request body'+str(event))
            }
        
        # Determinar si el body ya está parseado o necesita ser parseado
        if isinstance(body_str, dict):
            # Ya es un diccionario, no necesita parsing
            body_json = body_str
        else:
            # Es un string, necesita parsing
            try:
                body_json = json.loads(body_str)
            except json.JSONDecodeError:
                return {
                    'statusCode': 400,
                    'body': json.dumps('Error: Invalid JSON format in request body')
                }
        
        # Verificar si hay una estructura anidada con 'body'
        if isinstance(body_json, dict) and 'body' in body_json:
            inner_body = body_json['body']
            
            # Si inner_body es un string (podría ser JSON anidado)
            if isinstance(inner_body, str):
                try:
                    # Intentar deserializar el string interno
                    parsed_inner_body = json.loads(inner_body)
                    function = parsed_inner_body.get('function')
                    texto = parsed_inner_body.get('texto')
                except json.JSONDecodeError:
                    # Si falla, usar los valores del nivel superior
                    function = body_json.get('function')
                    texto = inner_body  # El string se trata como texto
            else:
                # Si inner_body ya es un diccionario
                function = inner_body.get('function')
                texto = inner_body.get('texto')
        else:
            # Formato plano: datos en el nivel superior
            function = body_json.get('function')
            texto = body_json.get('texto')
        
        # Verificar que tenemos los datos necesarios
        if not function or not texto:
            return {
                'statusCode': 400,
                'body': json.dumps('Error: Missing required fields (function or texto)')
            }
        
        # Redirigir según el tipo de función
        if function == "detectSensitiveData":
            return handle_sensitive_data_detection(texto)
        elif function == "claudia":
            return handle_claudia_chat(texto)
        else:
            return {
                'statusCode': 400,
                'body': json.dumps(f'Error: Unknown function type "{function}"')
            }
                    
    except Exception as e:
        print(f"Error inesperado en lambda_handler: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error inesperado: {str(e)}')
        }

def handle_sensitive_data_detection(body_text: str):
    """
    Maneja la detección de datos sensibles en el texto proporcionado.
    Esta es la funcionalidad original.
    """
    try:
        # Validar entrada
        if not body_text:
            return {
                'statusCode': 400,
                'body': json.dumps('Error: Empty text for sensitive data detection'+body_text)
            }
            
        # Dividir el documento en párrafos y después chunks
        paragraphs = body_text.split("\r")
        print(f"Documento dividido en {len(paragraphs)} párrafos")
        chunks = create_chunks(paragraphs, CHUNK_SIZE)
        print(f"Párrafos agrupados en {len(chunks)} chunks")

        # Procesar chunks en paralelo en ambas fases
        results_fase1, results_fase2 = process_chunks_in_parallel_two_phases(chunks, MAX_WORKERS)

        # Combinar todos los resultados de ambas fases
        output = combine_results_two_phases(results_fase1, results_fase2)

        return {
            'statusCode': 200,
            'body': json.dumps(output)
        }
    except Exception as e:
        print(f"Error en handle_sensitive_data_detection: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error procesando datos sensibles: {str(e)}')
        }

def handle_claudia_chat(prompt: str):
    """
    Maneja las interacciones de chat con ClaudIA.
    Esta es la nueva funcionalidad.
    """
    try:
        # Validar entrada
        if not prompt or not prompt.strip():
            return {
                'statusCode': 400,
                'body': json.dumps('Error: Empty prompt for ClaudIA chat')
            }
        
        print(f"Procesando prompt de chat: {prompt[:100]}...")
        
        # Llamar al modelo LLM para obtener respuesta
        response = invoke_claudia_model(prompt)
        
        # Devolver la respuesta como string dentro del body de la respuesta
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json; charset=utf-8',  # Agregar charset=utf-8
                'Access-Control-Allow-Origin': '*'  # Para permitir CORS
            },
            'body': json.dumps(response, ensure_ascii=False)  # ensure_ascii=False es clave
        }
    except Exception as e:
        print(f"Error en handle_claudia_chat: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json; charset=utf-8',  # Agregar charset=utf-8
                'Access-Control-Allow-Origin': '*'  # Para permitir CORS
            },
            'body': json.dumps(f'Error procesando chat con ClaudIA: {str(e)}', ensure_ascii=False)
        }

def invoke_claudia_model(prompt: str) -> str:
    """
    Invoca al modelo de lenguaje para generar una respuesta al prompt proporcionado.
    """
    try:
        # Preparar parámetros para la invocación del modelo
        # Nota: Se usa el mismo modelo que para la detección de datos sensibles
        kwargs = {
            "modelId": "eu.mistral.pixtral-large-2502-v1:0",
            "contentType": "application/json",
            "accept": "application/json",
            "body": json.dumps({
                "prompt": prompt,
                "max_tokens": 4000,  # Mayor límite para respuestas más completas
                "temperature": 0.7,  # Mayor temperatura para respuestas más creativas
                "top_p": 0.9  # Control adicional para mantener coherencia
            })
        }
        
        # Invocar al modelo
        response = bedrock_runtime.invoke_model(**kwargs)
        response_body = json.loads(response.get('body').read())
        output_text = response_body['choices'][0]['message']['content']
        print(output_text)

        # Limpiar la respuesta eliminando los caracteres \n
        if isinstance(output_text, str):
            # Reemplazar saltos de línea reales con espacios
            output_text = output_text.replace('\n', ' ')
            # Reemplazar secuencias de escape \n con espacios (por si acaso)
            output_text = output_text.replace('\\n', ' ')

            # Eliminar comillas iniciales y finales si existen
            if output_text.startswith('"') and output_text.endswith('"'):
                output_text = output_text[1:-1]
            # También manejar el caso donde solo hay comillas al inicio o al final
            elif output_text.startswith('"'):
                output_text = output_text[1:]
            elif output_text.endswith('"'):
                output_text = output_text[:-1]

        print(f"Respuesta generada: {output_text[:100]}...")
        return output_text
        
    except Exception as e:
        print(f"Error invocando modelo ClaudIA: {str(e)}")
        raise e

def process_chunk_fase1(chunk: str) -> Dict[str, List[str]]:
    """
    Procesa un chunk individual enviándolo a Bedrock para la fase 1 (datos personales).
    """
    try:
        prompt = formateo_call_datos_personales(chunk)
        
        kwargs = {
            "modelId": "eu.mistral.pixtral-large-2502-v1:0",
            "contentType": "application/json",
            "accept": "application/json",
            "body": json.dumps({
                "prompt": prompt, 
                "max_tokens": 2000, 
                "temperature": 0
            })
        }
        
        response = bedrock_runtime.invoke_model(**kwargs)
        response_body = json.loads(response.get('body').read())
        output_text = response_body['choices'][0]['message']['content']
        
        # Parsear el resultado JSON del texto de salida
        json_match = re.search(r'\{.*\}', output_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            result = json.loads(json_str)
            return result
        else:
            print(f"No se encontró JSON en la respuesta fase 1: {output_text[:100]}...")
            return create_empty_result_template_fase1()
            
    except Exception as e:
        print(f"Error procesando chunk en fase 1: {str(e)}")
        print(f"Contenido del chunk: {chunk[:100]}...")
        return create_empty_result_template_fase1()

def process_chunk_fase2(chunk: str) -> Dict[str, List[str]]:
    """
    Procesa un chunk individual enviándolo a Bedrock para la fase 2 (datos contextuales).
    """
    try:
        prompt = formateo_call_datos_contextuales(chunk)
        
        kwargs = {
            "modelId": "eu.mistral.pixtral-large-2502-v1:0",
            "contentType": "application/json",
            "accept": "application/json",
            "body": json.dumps({
                "prompt": prompt, 
                "max_tokens": 2000, 
                "temperature": 0
            })
        }
        
        response = bedrock_runtime.invoke_model(**kwargs)
        response_body = json.loads(response.get('body').read())
        output_text = response_body['choices'][0]['message']['content']
        
        # Parsear el resultado JSON del texto de salida
        json_match = re.search(r'\{.*\}', output_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            result = json.loads(json_str)
            return result
        else:
            print(f"No se encontró JSON en la respuesta fase 2: {output_text[:100]}...")
            return create_empty_result_template_fase2()
            
    except Exception as e:
        print(f"Error procesando chunk en fase 2: {str(e)}")
        print(f"Contenido del chunk: {chunk[:100]}...")
        return create_empty_result_template_fase2()

def process_chunks_in_parallel_two_phases(chunks: List[str], max_workers: int) -> Tuple[List[Dict[str, List[str]]], List[Dict[str, List[str]]]]:
    """
    Procesa múltiples chunks en paralelo para ambas fases utilizando un pool de hilos.
    """
    results_fase1 = []
    results_fase2 = []
    
    # Determinar el número óptimo de trabajadores (no más que el número de chunks)
    effective_workers = min(max_workers, len(chunks))
    
    print(f"Iniciando procesamiento paralelo fase 1 con {effective_workers} trabajadores")
    
    # Fase 1: Procesar datos personales
    with concurrent.futures.ThreadPoolExecutor(max_workers=effective_workers) as executor:
        future_to_chunk = {executor.submit(process_chunk_fase1, chunk): i for i, chunk in enumerate(chunks)}
        
        for future in concurrent.futures.as_completed(future_to_chunk):
            chunk_index = future_to_chunk[future]
            try:
                result = future.result()
                print(f"Fase 1: Chunk {chunk_index + 1}/{len(chunks)} procesado exitosamente")
                results_fase1.append(result)
            except Exception as e:
                print(f"Error en fase 1, chunk {chunk_index + 1}/{len(chunks)}: {str(e)}")
                results_fase1.append(create_empty_result_template_fase1())
    
    print(f"Iniciando procesamiento paralelo fase 2 con {effective_workers} trabajadores")
    
    # Fase 2: Procesar datos contextuales
    with concurrent.futures.ThreadPoolExecutor(max_workers=effective_workers) as executor:
        future_to_chunk = {executor.submit(process_chunk_fase2, chunk): i for i, chunk in enumerate(chunks)}
        
        for future in concurrent.futures.as_completed(future_to_chunk):
            chunk_index = future_to_chunk[future]
            try:
                result = future.result()
                print(f"Fase 2: Chunk {chunk_index + 1}/{len(chunks)} procesado exitosamente")
                results_fase2.append(result)
            except Exception as e:
                print(f"Error en fase 2, chunk {chunk_index + 1}/{len(chunks)}: {str(e)}")
                results_fase2.append(create_empty_result_template_fase2())
    
    return results_fase1, results_fase2

def combine_results_two_phases(results_fase1: List[Dict[str, List[str]]], results_fase2: List[Dict[str, List[str]]]) -> Dict[str, List[str]]:
    """
    Combina los resultados de ambas fases de todos los chunks en un solo resultado,
    eliminando duplicados y manteniendo el orden.
    """
    if not results_fase1 and not results_fase2:
        return create_empty_result_template_combined()
    
    # Inicializar el resultado combinado con la estructura completa
    combined = create_empty_result_template_combined()
    
    # Procesar resultados de la fase 1
    for key in create_empty_result_template_fase1().keys():
        unique_items = set()
        for result in results_fase1:
            if key in result and isinstance(result[key], list):
                for item in result[key]:
                    if item and item not in unique_items:
                        unique_items.add(item)
                        combined[key].append(item)
    
    # Procesar resultados de la fase 2
    for key in create_empty_result_template_fase2().keys():
        unique_items = set()
        for result in results_fase2:
            if key in result and isinstance(result[key], list):
                for item in result[key]:
                    if item and item not in unique_items:
                        unique_items.add(item)
                        combined[key].append(item)
    
    print(f"Combinación completada. Estadísticas de elementos encontrados:")
    for key, values in combined.items():
        print(f"  - {key}: {len(values)} elementos")
    
    return combined