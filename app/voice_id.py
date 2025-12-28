import json
from pathlib import Path
import torch
import torch.nn.functional as F
from speechbrain.inference.speaker import EncoderClassifier

from app.audio_utils import load_audio_ffmpeg

DB_PATH = Path("data/voice_db.json")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

_classifier = EncoderClassifier.from_hparams(
    source="speechbrain/spkrec-ecapa-voxceleb",
    run_opts={"device": "cpu"},
)

SR = 16000

def _load_db():
    if DB_PATH.exists():
        return json.loads(DB_PATH.read_text(encoding="utf-8"))
    return {"students": []}

def _save_db(db):
    DB_PATH.write_text(json.dumps(db, indent=2), encoding="utf-8")

def _embed(audio_path: str) -> torch.Tensor:
    wav = load_audio_ffmpeg(audio_path, sr=SR)          # [1, T]
    emb = _classifier.encode_batch(wav)                 # often [1, 1, D] or [1, D]
    emb = emb.squeeze()                                 # remove all size-1 dims
    emb = emb.flatten()                                 # ensure shape [D]
    return emb


def register_student(name: str, audio_path: str):
    emb = _embed(audio_path).tolist()
    db = _load_db()

    # find existing student
    for s in db["students"]:
        if s["name"].lower() == name.lower():
            s.setdefault("embeddings", [])
            # migrate old single embedding format if needed
            if "embedding" in s and "embeddings" not in s:
                s["embeddings"] = [s["embedding"]]
                del s["embedding"]

            s["embeddings"].append(emb)
            _save_db(db)
            return

    # new student
    db["students"].append({"name": name, "embeddings": [emb]})
    _save_db(db)

def identify_speaker(audio_path: str, threshold: float = 0.60):
    db = _load_db()
    if not db["students"]:
        return None

    emb = _embed(audio_path)

    best_name = None
    best_score = -1.0

    for s in db["students"]:
        embs = s.get("embeddings")

        # backward compatibility
        if embs is None and "embedding" in s:
            embs = [s["embedding"]]

        for e in embs:
            ref = torch.tensor(e).squeeze().flatten()
            score = F.cosine_similarity(emb, ref, dim=0).item()
            if score > best_score:
                best_score = score
                best_name = s["name"]

    # Debug (optional — you can remove later)
    print(f"VoiceID best match: {best_name} score={best_score:.3f} threshold={threshold}")

    return best_name if best_score >= threshold else None
