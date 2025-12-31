import json
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple


PACK_DIR = Path("curriculum_packs")


def _load_pack(pack_id: str) -> Dict[str, Any]:
    path = PACK_DIR / f"{pack_id}.json"
    if not path.exists():
        raise FileNotFoundError(
            f"Curriculum pack not found: {path}. "
            "Run: python tools/build_curriculum_packs.py"
        )
    return json.loads(path.read_text(encoding="utf-8"))


def _tokenize(text: str) -> List[str]:
    # Keep it simple: letters/numbers, remove very short words
    words = re.findall(r"[a-z0-9]+", text.lower())
    stop = {
        "the", "and", "or", "a", "an", "to", "of", "in", "on", "for", "with",
        "is", "are", "was", "were", "be", "been", "being", "this", "that",
        "it", "as", "at", "by", "from", "we", "you", "i", "they", "them",
        "do", "does", "did", "what", "why", "how", "when", "where", "explain",
        "please", "tell", "me"
    }
    return [w for w in words if len(w) >= 3 and w not in stop]


def retrieve_curriculum_chunks(
    pack_id: str,
    query: str,
    top_k: int = 4,
    max_chunk_chars: int = 900,
) -> List[Dict[str, str]]:
    """
    Keyword-based retrieval: score chunks by overlap with query tokens.
    Returns list of {chunk_id, text}.
    """
    pack = _load_pack(pack_id)
    chunks = pack.get("chunks", [])

    q_tokens = set(_tokenize(query))
    if not q_tokens:
        return []

    scored: List[Tuple[int, Dict[str, Any]]] = []
    for ch in chunks:
        text = ch.get("text", "")
        tokens = set(_tokenize(text))
        score = len(q_tokens.intersection(tokens))
        if score > 0:
            scored.append((score, ch))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = [ch for _, ch in scored[:top_k]]

    out = []
    for ch in top:
        t = (ch.get("text") or "").strip()
        if len(t) > max_chunk_chars:
            t = t[: max_chunk_chars - 3] + "..."
        out.append({"chunk_id": ch.get("chunk_id", ""), "text": t})
    return out


def pick_pack_id(student: dict) -> str:
    """
    MVP pack selection:
    - prefer explicit student['curriculum_pack']
    - else choose based on subject + year band
    """
    if student.get("curriculum_pack"):
        return student["curriculum_pack"]

    subject = (student.get("subject") or "").lower()

    # MVP: map Year 7/KS3 subjects to KS3 packs
    if "math" in subject:
        return "KS3_Maths"
    if "english" in subject:
        return "KS3_English"
    if "science" in subject:
        return "KS3_Science"

    # default fallback
    return "KS3_Maths"
