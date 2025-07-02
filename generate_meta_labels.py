import json
import numpy as np
def construir_meta_etiqueta(buffer, embeddings, group_labels, save_path="meta_labels.json"):
    """
    Construye etiquetas meta para todos los chunks, incluyendo loneliners como un grupo especial.
    
    Args:
        buffer: List[str] - textos originales
        embeddings: List[List[float]] - lista de embeddings
        group_labels: Dict[frozenset, str] - grupos con etiquetas generadas
        save_path: str - ruta de guardado
    
    Returns:
        Dict[int, Dict] - etiquetas meta por chunk
    """
    try:
        id_contract = np.random.randint(1, 1000)
        meta_labels = {}

        # Construir un índice inverso: chunk_id → lista de grupos con nombre
        chunk_to_groups = {i: [] for i in range(len(buffer))}
        for group_set, label in group_labels.items():
            for idx in group_set:
                chunk_to_groups[idx].append(label)

        for i, text in enumerate(buffer):
            try:
                paragraph_data = {
                    "id_contract": id_contract + i,
                    "embedding": embeddings[i],
                    "meta": {
                        "groups_related": chunk_to_groups[i] if chunk_to_groups[i] else ["loneliners"],
                        "text": text
                    }
                }
                meta_labels[i] = paragraph_data
            except Exception as e:
                print(f"Error processing paragraph {i}: {e}")

        # Guardar JSON
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(meta_labels, f, ensure_ascii=False, indent=2)
            print(f"Guardadas {len(meta_labels)} etiquetas meta en '{save_path}'")
        except Exception as e:
            print(f"Error saving meta labels to file '{save_path}': {e}")
        
        return meta_labels

    except Exception as e:
        print(f"Error in construir_meta_etiqueta: {e}")
        return None
