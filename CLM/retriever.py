import json
import os
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from generate_embeddings import get_embedding  # Usa el mismo modelo OpenAI
from collections import defaultdict
from openai import OpenAI
from dotenv import load_dotenv

class HybridRetriever:
    def __init__(self, model_client, base_path="models/", embedding_model="text-embedding-3-small"):
        self.client = model_client
        self.embedding_model = embedding_model
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        base_path = os.path.join(BASE_DIR, base_path)
        # Cargar datos
        self.chunk_data = self._load_json(os.path.join(base_path, "embeddings.json"))
        self.semantic_groups = self._load_json(os.path.join(base_path, "semantic_groups.json"))
        self.meta_labels = self._load_json(os.path.join(base_path, "meta_labels.json"))
        self.relations = self._load_json(os.path.join(base_path, "relations.json"))

        # Mapeo chunk → texto
        self.chunk_texts = {int(entry["id"]): entry["text"] for entry in self.chunk_data}
        # Mapeo grupo → lista de chunk_ids
        self.group_to_chunks = {
            group["group_name"]: group["indices"]
            for group in self.semantic_groups
        }
        # Mapeo grupo → embedding (centroide)
        self.group_embeddings = self._compute_group_embeddings()

    def _load_json(self, path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _compute_group_embeddings(self):
        group_embs = {}
        for group, chunk_ids in self.group_to_chunks.items():
            vectors = [self.chunk_data[i]["embedding"] for i in chunk_ids]
            group_embs[group] = np.mean(vectors, axis=0).tolist()
        return group_embs

    def retrieve_context(self,query, top_k=5, include_neighbors=True, sim_threshold=0.5, force_loneliners=3):
        query_emb = get_embedding(query, self.client, model=self.embedding_model)

        # Calcular similitud entre query y cada grupo
        group_scores = []
        for group, group_emb in self.group_embeddings.items():
            sim = cosine_similarity([query_emb], [group_emb])[0][0]
            group_scores.append((group, sim))

        # === FASE 1: Recuperar top_k grupos densos ===
        dense_groups = [
            (g, s) for g, s in group_scores if len(self.group_to_chunks.get(g, [])) > 1 and s >= sim_threshold
        ]
        dense_groups = sorted(dense_groups, key=lambda x: x[1], reverse=True)[:top_k]
        selected_groups = set(g for g, _ in dense_groups)

        # === FASE 2: Añadir los loneliners más similares ===
        loneliner_scores = [
            (g, s) for g, s in group_scores if len(self.group_to_chunks.get(g, [])) == 1
        ]
        top_loneliners = sorted(loneliner_scores, key=lambda x: x[1], reverse=True)[:force_loneliners]
        for loneliner, _ in top_loneliners:
            selected_groups.add(loneliner)

        # === EXPANSIÓN DE VECINOS EN EL GRAFO ===
        if include_neighbors:
            neighbors = set()
            for g in selected_groups:
                neighbors |= set(self.relations.get(g, {}).keys())
            selected_groups |= neighbors

        # === Recuperar chunks asociados ===
        relevant_chunk_ids = set()
        for group in selected_groups:
            chunk_ids = self.group_to_chunks.get(group, [])
            relevant_chunk_ids.update(chunk_ids)

        # === Extraer texto y grupos relacionados ===
        results = [{
            "chunk_id": cid,
            "text": self.chunk_texts[cid],
            "groups": self.meta_labels[str(cid)]["meta"].get("groups_related", [])
        } for cid in sorted(relevant_chunk_ids)]

        return results


#load_dotenv()
#client = OpenAI()
#retriever = HybridRetriever(client)

#query = "Let me know on which date delay liquidated damages will start accruing under this agreement. Please complement your answer with a reference to the relevant clauses under the Agreement."
#context_chunks = retriever.retrieve_context(query, top_k=5)

#for c in context_chunks:
    #print(f"Chunk {c['chunk_id']} | Groups: {c['groups']}\n{c['text']}\n")
