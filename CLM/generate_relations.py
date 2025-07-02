import numpy as np
import concurrent.futures
import itertools
import os
import json
from tqdm import tqdm
import time
from sklearn.metrics.pairwise import cosine_similarity


def get_representative_chunks(group_name, meta_labels, embeddings, buffer, top_k=2):
    # Obtener índices del grupo
    group_indices = [int(i) for i, d in meta_labels.items()
                     if group_name in d["meta"].get("groups_related", [])]

    # Extraer embeddings del grupo
    group_embs = [embeddings[i] for i in group_indices]
    group_matrix = np.array(group_embs)

    # Calcular centroide
    centroid = np.mean(group_matrix, axis=0)
    distances = np.linalg.norm(group_matrix - centroid, axis=1)

    # Obtener top N más cercanos
    sorted_indices = np.argsort(distances)

    # Aplicar criterio de longitud
    top_sorted = sorted(
        [(i, buffer[group_indices[i]]) for i in sorted_indices[:top_k*3]],
        key=lambda x: len(x[1]),
        reverse=True
    )[:top_k]

    # Devolver los textos seleccionados
    return [text for _, text in top_sorted]


def process_relationship(group_a, group_b, text_a, text_b, client):
    """
    Procesa la relación entre dos grupos con sus textos representativos.
    """
    try:
        prompt = (
            "You are an EPC legal assistant. Below are excerpts from two groups of contract clauses.\n"
            "Each group consists of semantically similar legal content.\n"
            "Identify and describe the key legal or functional relationship between the two groups,\n"
            "using a short, ontological label.\n\n"
            f"Group A – '{group_a}':\n" + "\n".join(f"- {chunk}" for chunk in text_a) + "\n\n"
            f"Group B – '{group_b}':\n" + "\n".join(f"- {chunk}" for chunk in text_b) + "\n\n"
            "Return only the relationship as a concise phrase (e.g., 'Contractual Dependency', 'Shared Trigger Event')."
        )

        response = client.responses.create(
            model="o4-mini-2025-04-16",
            input=[
                {"role": "system", "content": "You are an expert in legal ontology and contract analysis."},
                {"role": "user", "content": prompt}
            ],
        )

        relation = response.output_text.strip()
        return group_a, group_b, relation

    except Exception as e:
        print(f"Error processing relationship between '{group_a}' and '{group_b}': {e}")
        return group_a, group_b, f"Error: {str(e)}"


def definir_relaciones(meta_labels, embeddings, buffer, client, max_workers=10, output_file="relations.json", min_chunks=4, similarity_threshold=0.75):

    def group_embedding(group_name):
        indices = [i for i, d in meta_labels.items() if group_name in d["meta"].get("groups_related", [])]
        if not indices:
            return None
        group_embs = [embeddings[i]["embedding"] if isinstance(embeddings[i], dict) else embeddings[i] for i in indices]
        return np.mean(group_embs, axis=0)

    start_time = time.time()
    relations = {}
    relationship_pairs = set()

    # Recolectar grupos con nombre (excluye loneliners)
    group_sizes = {}
    for d in meta_labels.values():
        for g in d["meta"].get("groups_related", []):
            if g != "loneliners":
                group_sizes[g] = group_sizes.get(g, 0) + 1

    all_groups = sorted(group_sizes.keys())

    # Calcular embeddings promedio por grupo (filtrando por tamaño mínimo)
    group_vectors = {
        #g: group_embedding(g) for g, size in group_sizes.items() if size >= min_chunks
        g: group_embedding(g) for g in group_sizes.keys()

    }

    # Generar combinaciones únicas y filtrar por similitud
    group_names = list(group_vectors.keys())
    for a, b in itertools.combinations(group_names, 2):
        emb_a, emb_b = group_vectors[a], group_vectors[b]
        if emb_a is None or emb_b is None:
            continue
        sim = cosine_similarity([emb_a], [emb_b])[0][0]
        if sim >= similarity_threshold:
            relationship_pairs.add((a, b))

    print(f"Found {len(relationship_pairs)} relevant group relationships to process")

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_pair = {}
        for group_a, group_b in relationship_pairs:
            text_a = get_representative_chunks(group_a, meta_labels, embeddings, buffer)
            text_b = get_representative_chunks(group_b, meta_labels, embeddings, buffer)
            future = executor.submit(process_relationship, group_a, group_b, text_a, text_b, client)
            future_to_pair[future] = (group_a, group_b)

        for future in tqdm(concurrent.futures.as_completed(future_to_pair), total=len(future_to_pair), desc="Processing relationships"):
            try:
                group_a, group_b, relation = future.result()
                if group_a not in relations:
                    relations[group_a] = {}
                relations[group_a][group_b] = relation
            except Exception as e:
                a, b = future_to_pair[future]
                print(f"Error retrieving result for pair ({a}, {b}): {e}")

    elapsed_time = time.time() - start_time
    print(f"Processed {sum(len(v) for v in relations.values())} relationships in {elapsed_time:.2f} seconds.")

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(relations, f, ensure_ascii=False, indent=2)
        print(f"Saved relationships to '{output_file}'")
    except Exception as e:
        print(f"Error saving relationships: {e}")

    return relations
