from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize
from sklearn.metrics.pairwise import cosine_distances


import numpy as np
import json
import os
import hdbscan



def calculate_distances(embeddings, buffer, save_path="distances.json"):
    """
    Calcula distancias basadas en cosine similarity entre pares de embeddings y guarda los resultados.
    
    Args:
        embeddings: List[List[float]] - lista de vectores de embedding.
        buffer: List[str] - textos originales correspondientes a cada embedding.
        save_path: str - ruta del archivo JSON de salida.
        
    Returns:
        List[Dict] con pares de texto y su distancia semántica.
    """
    if isinstance(embeddings[0], dict):
        embeddings = [e["embedding"] for e in embeddings]

    # Convertimos la lista de listas a matriz numpy para eficiencia
    X = np.array(embeddings)
    
    # Calculamos la matriz de similitud coseno
    similarity_matrix = cosine_similarity(X)
    
    results = []
    n = len(buffer)
    
    for i in range(n):
        for j in range(i + 1, n):
            sim = similarity_matrix[i, j]
            distance = 1 - sim  # entre 0 (idéntico) y 2 (opuesto)
            results.append({
                "text_pair": [buffer[i], buffer[j]],
                "distance": round(distance, 5)
            })
    
    # Guardamos resultados
    with open(save_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"Guardados {len(results)} pares de distancias en '{save_path}'")
    return results


def agrupamiento_semantico(embeddings, buffer, min_cluster_size=2, min_samples=1, 
                         cluster_selection_epsilon=0.0, cluster_selection_method='eom',
                         save_path="semantic_groups.json"):
    """
    Agrupa semánticamente los embeddings usando HDBSCAN con parámetros optimizados.
    
    Args:
        embeddings: List[List[float]], lista de embeddings.
        buffer: List[str], textos originales.
        min_cluster_size: int, tamaño mínimo de grupo (reducir para más grupos).
        min_samples: int, número mínimo de muestras en un núcleo (reducir para más grupos).
        cluster_selection_epsilon: float, umbral de epsilon para selección de clusters.
        cluster_selection_method: str, método de selección ('eom' o 'leaf').
        save_path: str, ruta del archivo JSON de salida.
    
    Returns:
        dist_matrix: np.ndarray de similitud coseno normalizada
        groups_text: List[List[str]] con los textos agrupados
        neighbor_groups: Set[frozenset] de índices agrupados
    """
    print("Realizando agrupamiento semántico con HDBSCAN...")

    # Preparamos los embeddings y calculamos matriz de distancias coseno
    X = np.array(embeddings)
    X_norm = normalize(X)  # Normalizar para cosine similarity
    
    # Calcular matriz de distancias coseno manualmente
    cosine_distances = 1 - np.dot(X_norm, X_norm.T)
    # Asegurar que la diagonal sea 0 y valores sean no negativos
    np.fill_diagonal(cosine_distances, 0)
    cosine_distances = np.maximum(cosine_distances, 0)

    # Configuración optimizada de HDBSCAN para más grupos
    clusterer = hdbscan.HDBSCAN(
        metric='precomputed',  # Usar matriz precomputada
        min_cluster_size=min_cluster_size,
        min_samples=min_samples,
        cluster_selection_epsilon=cluster_selection_epsilon,
        cluster_selection_method=cluster_selection_method,
        allow_single_cluster=False,  # Evita que todo se agrupe en un solo cluster
    )
    
    labels = clusterer.fit_predict(cosine_distances)

    # Analizar la calidad del clustering
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise = list(labels).count(-1)
    
    print(f"Número de clusters encontrados: {n_clusters}")
    print(f"Número de puntos de ruido: {n_noise}")
    print(f"Porcentaje de clustering: {((len(labels) - n_noise) / len(labels)) * 100:.1f}%")

    groups = {}
    for idx, label in enumerate(labels):
        if label == -1:
            group_name = f"group_loneliner_{idx}"
        else:
            group_name = f"group_{label}"
        groups.setdefault(group_name, []).append(idx)

    # Convertimos los grupos a formato exportable
    groups_with_indices = []
    for group_name, indices in groups.items():
        paragraphs = [buffer[i] for i in sorted(indices)]
        groups_with_indices.append({
            "group_name": group_name,
            "indices": sorted(indices),
            "paragraphs": paragraphs
        })

    # Guardamos en JSON
    with open(save_path, 'w', encoding='utf-8') as f:
        json.dump(groups_with_indices, f, ensure_ascii=False, indent=2)

    print(f"Guardados {len(groups_with_indices)} grupos semánticos en '{save_path}'")
    print(f"Número de grupos con más de 2 chunks: {len([g for g in groups_with_indices if len(g['indices']) > 2])}")
    
    # Devolvemos estructuras útiles para pasos siguientes
    dist_matrix = 1 - np.dot(X_norm, X_norm.T)  # matriz de "distancias" coseno
    groups_text = [group["paragraphs"] for group in groups_with_indices]
    neighbor_groups = {frozenset(group["indices"]) for group in groups_with_indices}

    return dist_matrix, groups_text, neighbor_groups
