import json
from pathlib import Path
from typing import Dict, Any

PLANS_DIR = Path("lesson_plans")


def load_plan(cohort_id: str) -> Dict[str, Any]:
    path = PLANS_DIR / f"{cohort_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"Lesson plan not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def get_lesson(plan: Dict[str, Any], unit_idx: int, lesson_idx: int) -> Dict[str, Any]:
    return plan["units"][unit_idx]["lessons"][lesson_idx]


def get_step(lesson: Dict[str, Any], step_idx: int) -> Dict[str, Any]:
    steps = lesson.get("steps", [])
    if step_idx >= len(steps):
        return {"type": "end", "text": "Lesson completed."}
    return steps[step_idx]
