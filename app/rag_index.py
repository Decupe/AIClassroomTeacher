from dotenv import load_dotenv
load_dotenv()

import json
import os
from pathlib import Path
from typing import Dict, Any, List

import numpy as np
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

PACK_DIR = Path("curriculum_packs")
INDEX_DIR = Path(".rag_index")
INDEX_DIR.mkdir(parents=True, exist_ok=True)




def _pack_path(pack_id: str) -> Path:
    return PACK_DIR / f"{pack_id}.json"


def _index_path(pack_id: str) -> Path:
    return INDEX_DIR / f"{pack_id}.index.json"


def load_pack(pack_id: str) -> Dict[str, Any]:
    path = _pack_path(pack_id)
    if not path.exists():
        raise FileNotFoundError(f"Missing pack: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def build_index(pack_id: str, model: str = "text-embedding-3-small") -> Path:
    """
    Builds embeddings for all chunks in a pack and stores them in .rag_index/<pack_id>.index.json
    """
    pack = load_pack(pack_id)
    chunks = pack.get("chunks", [])
    if not chunks:
        raise ValueError(f"No chunks found in {pack_id}")

    # Batch embeddings
    texts = [c["text"] for c in chunks]
    chunk_ids = [c["chunk_id"] for c in chunks]

    # OpenAI embeddings API supports batching
    resp = client.embeddings.create(model=model, input=texts)
    vectors = [d.embedding for d in resp.data]

    out = {
        "pack_id": pack_id,
        "embedding_model": model,
        "chunks": [{"chunk_id": cid, "embedding": vec} for cid, vec in zip(chunk_ids, vectors)],
    }

    path = _index_path(pack_id)
    path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    return path


def load_index(pack_id: str) -> Dict[str, Any]:
    path = _index_path(pack_id)
    if not path.exists():
        raise FileNotFoundError(
            f"Index not found for {pack_id}. Build it with: python -m app.build_rag_index {pack_id}"
        )
    return json.loads(path.read_text(encoding="utf-8"))


def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)
