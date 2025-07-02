import os
import json
import concurrent.futures
from tqdm import tqdm



def extracting_and_chunking():     
    content_clean = []
    # Open the file and read its content
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, "Listado de párrafos EPC.txt")
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()
        content = content.splitlines()
    # Remove empty lines and lines with less than 3 characters
    for line in content: 
        if len(line) > 3:
            content_clean.append(line)
    # Generate chunks of 2 paragraphs each 
    buffer = []
    for i in range(0, len(content_clean), 2):
        buffer.append(" ".join(content_clean[i:i+2]))

    return buffer


def get_embedding(text, client, model="text-embedding-3-small"):
    """
    Llama el endpoint de embeddings de OpenAI para un texto dado.
    - text: str, texto al que calcular embedding.
    - client: instancia de OpenAI client configurada con tu API key.
    - model: nombre del modelo de embeddings.
    Returns: List[float] embedding de dimensión d.
    """
    clean_text = text.replace("\n", " ")
    resp = client.embeddings.create(input=[clean_text], model=model)
    return resp.data[0].embedding

def calculate_chunk_embeddings(buffer, client, model="text-embedding-3-small", save_path="chunk_embeddings.json", max_workers=10):
    """
    Calcula los embeddings para cada chunk de texto de forma concurrente y los guarda en un JSON en el mismo directorio del script.

    Args:
        buffer: List[str], chunks de texto
        client: instancia de OpenAI client
        model: modelo de embeddings
        save_path: nombre del archivo de salida (solo nombre, no path)
        max_workers: número máximo de hilos a usar

    Returns:
        List[Dict] con campos 'id', 'text', 'embedding'
    """
    def embed_chunk(i_text):
        i, text = i_text
        try:
            emb = get_embedding(text, client, model)
            return {
                "id": i,
                "text": text,
                "embedding": emb
            }
        except Exception as e:
            print(f"Error embedding chunk {i}: {e}")
            return None

    print(f"Generando embeddings con {max_workers} hilos...")

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(tqdm(executor.map(embed_chunk, enumerate(buffer)), total=len(buffer)))

    # Filtramos posibles None por errores
    results = [r for r in results if r is not None]

    # Guardar archivo en el mismo directorio del script
    base_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(base_dir, save_path)

    with open(full_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"Guardados {len(results)} chunks embebidos en '{full_path}'")
    return results