import json
from pathlib import Path
from typing import Any, Dict

from app.lesson_plan import load_plan, get_lesson, get_step


STATE_PATH = Path("data/classroom_state.json")


def _ensure_data_dir() -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)


def _load_state() -> Dict[str, Any]:
    _ensure_data_dir()
    if not STATE_PATH.exists():
        return {"cohorts": {}}
    return json.loads(STATE_PATH.read_text(encoding="utf-8"))


def _save_state(state: Dict[str, Any]) -> None:
    _ensure_data_dir()
    STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def get_or_create_cohort_state(cohort_id: str) -> Dict[str, int]:
    """
    Keeps track of where the class is: unit -> lesson -> step.
    """
    state = _load_state()
    cohorts = state.setdefault("cohorts", {})

    if cohort_id not in cohorts:
        cohorts[cohort_id] = {"unit_idx": 0, "lesson_idx": 0, "step_idx": 0}

    _save_state(state)
    return cohorts[cohort_id]


def reset_cohort(cohort_id: str) -> None:
    """
    Reset a cohort back to the first unit/lesson/step.
    """
    state = _load_state()
    cohorts = state.setdefault("cohorts", {})
    cohorts[cohort_id] = {"unit_idx": 0, "lesson_idx": 0, "step_idx": 0}
    _save_state(state)


def advance_step(cohort_id: str) -> None:
    """
    Advances in an orderly way:
    step -> next step
    end of steps -> next lesson
    end of lessons -> next unit
    end of units -> stay at final step (end)
    """
    plan = load_plan(cohort_id)
    units = plan.get("units", [])
    if not units:
        return

    state = _load_state()
    cohorts = state.setdefault("cohorts", {})
    cohort = cohorts.get(cohort_id) or {"unit_idx": 0, "lesson_idx": 0, "step_idx": 0}

    unit_idx = int(cohort.get("unit_idx", 0))
    lesson_idx = int(cohort.get("lesson_idx", 0))
    step_idx = int(cohort.get("step_idx", 0))

    # Clamp indices safely
    unit_idx = max(0, min(unit_idx, len(units) - 1))
    lessons = units[unit_idx].get("lessons", [])
    if not lessons:
        return
    lesson_idx = max(0, min(lesson_idx, len(lessons) - 1))

    lesson = get_lesson(plan, unit_idx, lesson_idx)
    steps = lesson.get("steps", [])
    if not steps:
        return
    step_idx = max(0, min(step_idx, len(steps) - 1))

    # If current step is an explicit "end", do not advance further
    current_step = get_step(lesson, step_idx)
    if current_step.get("type") == "end":
        cohorts[cohort_id] = {"unit_idx": unit_idx, "lesson_idx": lesson_idx, "step_idx": step_idx}
        _save_state(state)
        return

    # Move to next step if possible
    if step_idx + 1 < len(steps):
        step_idx += 1
    else:
        # Move to next lesson
        if lesson_idx + 1 < len(lessons):
            lesson_idx += 1
            step_idx = 0
        else:
            # Move to next unit
            if unit_idx + 1 < len(units):
                unit_idx += 1
                lesson_idx = 0
                step_idx = 0
            else:
                # End of the entire plan: stay at final lesson final step
                unit_idx = len(units) - 1
                lessons = units[unit_idx].get("lessons", [])
                lesson_idx = len(lessons) - 1 if lessons else 0
                lesson = get_lesson(plan, unit_idx, lesson_idx)
                steps = lesson.get("steps", [])
                step_idx = len(steps) - 1 if steps else 0

    cohorts[cohort_id] = {"unit_idx": unit_idx, "lesson_idx": lesson_idx, "step_idx": step_idx}
    _save_state(state)
