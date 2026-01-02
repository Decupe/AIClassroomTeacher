from pathlib import Path

from app.stt_local import transcribe
from app.tts_local import speak
from app.voice_id import identify_speaker

from app.memory import get_student_memory, update_student_progress, build_memory_summary

from app.lesson_plan import load_plan, get_lesson, get_step
from app.classroom_state import get_or_create_cohort_state, advance_step

from app.teacher_openai import (
    teacher_welcome,
    teacher_teach_step,
    teacher_answer_question_and_resume,
)

# Cohort / class we are teaching (matches lesson_plans/Year7_Maths_Term1.json)
COHORT_ID = "Year7_Maths_Term1"

STUDENT = {
    "age": 12,
    "class": "Year 7",
    "subject": "Maths",
    "level": "beginner",
    "learning_style": "step-by-step",
}


def find_audio_file() -> Path:
    candidates = [
        Path("samples/student_question.wav"),
        Path("samples/student_question.m4a"),
        Path("samples/student_question.wav.m4a"),
        Path("samples/student_question.mp3"),
    ]
    for p in candidates:
        if p.exists():
            return p
    raise FileNotFoundError(
        "No audio file found. Put one of these in samples/: "
        "student_question.wav / student_question.m4a / student_question.mp3"
    )


def _reload_plan_state_step():
    """Reload plan/state/lesson/step based on current cohort_state (single source of truth)."""
    plan = load_plan(COHORT_ID)
    cohort_state = get_or_create_cohort_state(COHORT_ID)
    lesson = get_lesson(plan, cohort_state["unit_idx"], cohort_state["lesson_idx"])
    step = get_step(lesson, cohort_state["step_idx"])
    return plan, cohort_state, lesson, step


def main() -> None:
    # 1) Audio input
    audio_path = find_audio_file()
    print(f"Using audio: {audio_path}")

    # 2) Identify student
    raw = identify_speaker(str(audio_path))
    print(f"Raw speaker match: {raw}")

    speaker = raw if raw else "Student"
    STUDENT["name"] = speaker
    print(f"Detected speaker (final): {speaker}")

    # 3) Load memory summary (optional)
    mem = get_student_memory(STUDENT["name"])
    STUDENT["memory_summary"] = build_memory_summary(mem)

    print(f"Detected speaker: {speaker}")

    # 4) Transcribe question
    question = transcribe(str(audio_path)).strip()
    print("\n--- TRANSCRIBED QUESTION ---")
    print(question if question else "[No question detected]")

    # 5) Load lesson plan + state + current step
    plan, cohort_state, lesson, step = _reload_plan_state_step()

    # 6) Welcome (later: do this once per day using memory)
    welcome = teacher_welcome(STUDENT, plan, cohort_state, lesson)
    print("\n--- TEACHER WELCOME ---")
    print(welcome)
    speak(welcome)

    # 7) If student asked a question, answer and then truly resume teaching
    if question:
        answer = teacher_answer_question_and_resume(
            STUDENT, plan, cohort_state, lesson, step, question
        )

        print("\n--- TEACHER ANSWER (Q&A) ---")
        print(answer)
        speak(answer)

        update_student_progress(
            name=STUDENT["name"],
            question=question,
            answer=answer,
            topic=plan.get("subject", STUDENT.get("subject")),
        )

        # ✅ KEY FIX:
        # After Q&A, move forward one step so "resume" actually continues.
        advance_step(COHORT_ID)

        # Reload the new current step (the one we should teach now)
        plan, cohort_state, lesson, step = _reload_plan_state_step()

    # 8) If we land on an end step, advance again to the next lesson/unit if possible
    # (Your advance_step() should handle rolling step_idx -> next lesson; if it doesn't,
    # we'll adjust classroom_state next.)
    if step.get("type") == "end":
        # Try to move into next lesson
        advance_step(COHORT_ID)
        plan, cohort_state, lesson, step = _reload_plan_state_step()

        # If still end, then the whole plan is done
        if step.get("type") == "end":
            end_msg = (
                f"{STUDENT['name']}, we have completed this term's lesson plan. Well done. "
                "Next time we can start a new term or subject."
            )
            print("\n--- LESSON STATUS ---")
            print(end_msg)
            speak(end_msg)
            return

    # 9) Teach the current step in order
    teach_text = teacher_teach_step(STUDENT, plan, cohort_state, lesson, step)

    print("\n--- TEACHING CURRENT STEP ---")
    print(teach_text)
    speak(teach_text)

    update_student_progress(
        name=STUDENT["name"],
        question=f"[LESSON_STEP] {lesson.get('lesson_title')} - step {cohort_state['step_idx'] + 1}",
        answer=teach_text,
        topic=plan.get("subject", STUDENT.get("subject")),
    )

    # 10) Advance for next session
    advance_step(COHORT_ID)
    print("\nAdvanced lesson step for next session ✅")


if __name__ == "__main__":
    main()
