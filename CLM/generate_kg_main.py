import json
import os
from dotenv import load_dotenv
from openai import OpenAI

from generate_embeddings import extracting_and_chunking, calculate_chunk_embeddings
from generate_semantic_groups import calculate_distances, agrupamiento_semantico
from naming_semantic_groups import generate_titles
from generate_meta_labels import construir_meta_etiqueta
from generate_relations import definir_relaciones
from generate_kg import generate_kgraph

# === CONFIGURACIÓN ===
EMBEDDING_MODEL = "text-embedding-3-small"
NAMING_MODEL = "o4-mini-2025-04-16"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.join(BASE_DIR, "models")
EMBEDDINGS_PATH = os.path.join(BASE_DIR, "embeddings.json")
DISTANCES_PATH = os.path.join(BASE_DIR, "distances.json")
SEMANTIC_GROUPS_PATH = os.path.join(BASE_DIR, "semantic_groups.json")
META_LABELS_PATH = os.path.join(BASE_DIR, "meta_labels.json")
RELATIONS_PATH = os.path.join(BASE_DIR, "relations.json")
KG_HTML_PATH = os.path.join(BASE_DIR, "kgraph.html")


load_dotenv()

# === INICIALIZAR CLIENTE OPENAI ===
client = OpenAI()

# === PASO 1: Chunking y Embeddings ===
print("[1/6] Extrayendo y embebiendo chunks...")
buffer = extracting_and_chunking()
embedding_dicts = calculate_chunk_embeddings(buffer, client, model=EMBEDDING_MODEL, save_path=EMBEDDINGS_PATH)
embeddings = [item["embedding"] for item in embedding_dicts]

# === PASO 2: Agrupamiento semántico ===
print("[2/6] Calculando distancias y agrupando semánticamente...")
calculate_distances(embeddings, buffer, save_path=DISTANCES_PATH)
dist_matrix, semantic_groups, neighbor_groups = agrupamiento_semantico(
    embeddings, buffer, save_path=SEMANTIC_GROUPS_PATH
)

# === PASO 3: Nombrado de grupos (solo si >2 chunks) ===
print("[3/6] Generando nombres de grupos relevantes...")
group_labels = generate_titles(neighbor_groups, client, buffer, model=NAMING_MODEL, max_workers=10)

# === PASO 4: Meta etiquetas por párrafo ===
print("[4/6] Generando meta etiquetas para cada chunk...")
meta_labels = construir_meta_etiqueta(buffer, embeddings, group_labels, save_path=META_LABELS_PATH)

# === PASO 5: Relaciones entre grupos ===
print("[5/6] Generando relaciones entre grupos semánticos...")
definir_relaciones(meta_labels, embeddings, buffer, client, max_workers=10, output_file=RELATIONS_PATH, min_chunks=4, similarity_threshold=0.75)

# === PASO 6: Grafo de conocimiento ===
print("[6/6] Generando visualización del grafo de conocimiento...")
with open(RELATIONS_PATH, "r", encoding="utf-8") as f:
    relations = json.load(f)

generate_kgraph(relations, meta_labels, client, group_labels, save_path=KG_HTML_PATH)

print("\n✅ Proceso completo. Grafo generado en:", KG_HTML_PATH)
