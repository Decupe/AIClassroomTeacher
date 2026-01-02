from dotenv import load_dotenv
load_dotenv()

import os
import numpy as np
from openai import OpenAI
from typing import List, Dict

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

from app.rag_index import load_pack, load_index, cosine_sim




def retrieve_semantic(pack_id: str, query: str, top_k: int = 4, max_chunk_chars: int = 900) -> List[Dict[str, str]]:
    pack = load_pack(pack_id)
    idx = load_index(pack_id)

    # Embed query
    q_resp = client.embeddings.create(model=idx["embedding_model"], input=query)
    q_vec = np.array(q_resp.data[0].embedding, dtype=np.float32)

    # Create map from chunk_id -> text
    text_map = {c["chunk_id"]: c["text"] for c in pack.get("chunks", [])}

    scored = []
    for item in idx["chunks"]:
        cid = item["chunk_id"]
        vec = np.array(item["embedding"], dtype=np.float32)
        score = cosine_sim(q_vec, vec)
        scored.append((score, cid))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:top_k]

    out = []
    for score, cid in top:
        t = (text_map.get(cid) or "").strip()
        if len(t) > max_chunk_chars:
            t = t[: max_chunk_chars - 3] + "..."
        out.append({"chunk_id": cid, "text": t})
    return out
