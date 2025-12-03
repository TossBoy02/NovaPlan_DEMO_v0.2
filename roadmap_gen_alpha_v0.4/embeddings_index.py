import os
import json
from pathlib import Path
from sentence_transformers import SentenceTransformer
import numpy as np
import faiss

MODEL_NAME = 'all-mpnet-base-v2'
EMBED_DIR = Path('embeddings')
EMBED_DIR.mkdir(exist_ok=True)

# Lazy-load model to avoid blocking app startup
_model = None


def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def build_skill_index(skill_texts: list[str], index_path: Path = EMBED_DIR / 'skill_index.faiss') -> dict:
    model = get_model()
    embeddings = model.encode(skill_texts, convert_to_numpy=True, show_progress_bar=True)
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    faiss.normalize_L2(embeddings)
    index.add(embeddings)
    faiss.write_index(index, str(index_path))
    # save mapping
    mapping = {'skills': skill_texts}
    with open(EMBED_DIR / 'skill_mapping.json','w',encoding='utf-8') as f:
        json.dump(mapping,f)
    return mapping


def load_skill_index(index_path: Path = EMBED_DIR / 'skill_index.faiss') -> tuple:
    index = faiss.read_index(str(index_path))
    with open(EMBED_DIR / 'skill_mapping.json','r',encoding='utf-8') as f:
        mapping = json.load(f)
    return index, mapping


def query_skill(skill_query: str, k=5):
    model = get_model()
    q_emb = model.encode([skill_query], convert_to_numpy=True)
    faiss.normalize_L2(q_emb)
    index, mapping = load_skill_index()
    D, I = index.search(q_emb, k)
    results = [mapping['skills'][i] for i in I[0]]
    return results, D[0]
