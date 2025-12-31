import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_PATH = Path("data/progress_db.json")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _ensure_data_dir() -> None:
    Path("data").mkdir(parents=True, exist_ok=True)


def _load_db() -> Dict[str, Any]:
    _ensure_data_dir()
    if not DB_PATH.exists():
        return {"students": {}}
    return json.loads(DB_PATH.read_text(encoding="utf-8"))


def _save_db(db: Dict[str, Any]) -> None:
    _ensure_data_dir()
    DB_PATH.write_text(json.dumps(db, indent=2, ensure_ascii=False), encoding="utf-8")


def get_student_memory(name: str) -> Dict[str, Any]:
    """
    Returns a memory object for a student (creates one if missing).
    """
    db = _load_db()
    students = db.setdefault("students", {})
    if name not in students:
        students[name] = {
            "name": name,
            "created_at": _utc_now_iso(),
            "last_seen_at": _utc_now_iso(),
            "topics": {},              # topic -> {"asked": int, "last": iso, "notes": str}
            "misconceptions": [],      # list[str]
            "strengths": [],           # list[str]
            "last_questions": [],      # list[{"ts":..., "q":..., "a_short":..., "topic":...}]
        }
        _save_db(db)
    return students[name]


def _cap_list(lst: List[Any], max_items: int) -> List[Any]:
    return lst[-max_items:]


def update_student_progress(
    name: str,
    question: str,
    answer: str,
    topic: Optional[str] = None,
    misconception: Optional[str] = None,
    strength: Optional[str] = None,
) -> None:
    """
    Updates memory after a Q&A. Topic/misconception/strength are optional for MVP.
    """
    db = _load_db()
    students = db.setdefault("students", {})
    student = students.get(name) or get_student_memory(name)

    student["last_seen_at"] = _utc_now_iso()

    # Topic tracking (simple)
    if topic:
        t = student["topics"].setdefault(topic, {"asked": 0, "last": None, "notes": ""})
        t["asked"] += 1
        t["last"] = _utc_now_iso()

    # Add misconception/strength (avoid duplicates, keep short lists)
    if misconception:
        if misconception not in student["misconceptions"]:
            student["misconceptions"].append(misconception)
        student["misconceptions"] = _cap_list(student["misconceptions"], 10)

    if strength:
        if strength not in student["strengths"]:
            student["strengths"].append(strength)
        student["strengths"] = _cap_list(student["strengths"], 10)

    # Store last questions (short answer excerpt)
    a_short = answer.strip().replace("\n", " ")
    if len(a_short) > 180:
        a_short = a_short[:177] + "..."

    student["last_questions"].append(
        {"ts": _utc_now_iso(), "q": question.strip(), "a_short": a_short, "topic": topic or ""}
    )
    student["last_questions"] = _cap_list(student["last_questions"], 8)

    students[name] = student
    _save_db(db)


def build_memory_summary(student_memory: Dict[str, Any]) -> str:
    """
    Creates a short summary for the teacher prompt.
    """
    topics = student_memory.get("topics", {})
    top_topics = sorted(topics.items(), key=lambda kv: kv[1].get("asked", 0), reverse=True)[:3]
    top_topics_text = ", ".join([f"{t}({meta.get('asked',0)})" for t, meta in top_topics]) or "None yet"

    misconceptions = student_memory.get("misconceptions", [])
    strengths = student_memory.get("strengths", [])

    last_qs = student_memory.get("last_questions", [])
    last_q_text = last_qs[-1]["q"] if last_qs else "None yet"

    return (
        f"Recent topic focus: {top_topics_text}\n"
        f"Known misconceptions: {', '.join(misconceptions) if misconceptions else 'None recorded'}\n"
        f"Strengths: {', '.join(strengths) if strengths else 'None recorded'}\n"
        f"Last question asked: {last_q_text}"
    )

