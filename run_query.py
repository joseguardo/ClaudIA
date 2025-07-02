# run_query.py

from retriever import HybridRetriever
from generator import generate_event
from verifier import verify_event_sources
from generate_calendar_vis import generate_contractual_calendar_html, load_calendar_from_file
from openai import OpenAI
from dotenv import load_dotenv
import json
import os

# === CONFIGURACIÓN ===
TOP_K_GROUPS = 10
NUM_LONELINERS = 3
SIM_THRESHOLD = 0.69
INCLUDE_NEIGHBORS = True
MODEL_NAME = "o4-mini-2025-04-16"
PROMPT_PATH = "prompts/generate_event_prompt.txt"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROMPT_PATH = os.path.join(BASE_DIR, PROMPT_PATH)
QUERIES_PATH = "models/queries.json"
QUERIES_PATH = os.path.join(BASE_DIR, QUERIES_PATH)


def run(query: str):
    # === Inicializar cliente y módulos ===
    load_dotenv()
    client = OpenAI()
    retriever = HybridRetriever(client)

    print("\n🔍 Recuperando chunks relevantes...")
    context_chunks = retriever.retrieve_context(
        query=query,
        top_k=TOP_K_GROUPS,
        sim_threshold=SIM_THRESHOLD,
        force_loneliners=NUM_LONELINERS,
        include_neighbors=INCLUDE_NEIGHBORS
    )
    print(f"✅ Recuperados {len(context_chunks)} chunks.\n")

    # === Generar evento(s) estructurado(s) ===
    print("🧠 Generando evento(s) a partir del contexto...")
    events = generate_event(
        query=query,
        context_chunks=context_chunks,
        client=client,
        model=MODEL_NAME,
        prompt_path=PROMPT_PATH
    )

    # Normalizar a lista
    if isinstance(events, dict):
        events = [events]

    print(f"✅ Generados {len(events)} evento(s).\n")

    # === Verificar fuentes del/los evento(s) ===
    print("🔍 Extrayendo citas del/los evento(s)...")
    verified = verify_event_sources(events, context_chunks)

    # === Mostrar resultado ===
    print("\n📦 EVENTOS GENERADOS:")
    for e in verified:
        print(json.dumps(e, indent=2, ensure_ascii=False))

    # === Mostrar contexto fuente ===
    print("\n📚 CHUNKS DE CONTEXTO UTILIZADOS:")
    for c in context_chunks:
        print(f"\nChunk {c['chunk_id']} (Groups: {', '.join(c['groups'])})")
        print(c['text'])

    return verified


if __name__ == "__main__":
    with open(QUERIES_PATH, "r", encoding="utf-8") as f:
        queries = json.load(f)
    calendar = []
    for q in queries:
        query = q["question"]
        print(f"\n\n=== Ejecutando query: {query} ===")
        events = run(query)
        for e in events:
            calendar.append(e)
    # Guardar calendario generado
    output_path = os.path.join(BASE_DIR, "generated_calendar.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(calendar, f, indent=2, ensure_ascii=False)
    print(f"✅ Calendario guardado en {output_path}")
    calendar_data = load_calendar_from_file("generated_calendar.json")
    html_content = generate_contractual_calendar_html(calendar_data)

    # Guardar HTML generado
    html_output_path = os.path.join(BASE_DIR, "generated_calendar.html")
    with open(html_output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"✅ Calendario HTML guardado en {html_output_path}")

    # Puedes reemplazar esta query por cualquiera del archivo de EPC
    # example_query = "Let me know on which date delay liquidated damages will start accruing under this agreement. Please complement your answer with a reference to the relevant clauses under the Agreement."
    # run(example_query)
