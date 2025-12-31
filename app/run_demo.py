from pathlib import Path

from app.stt_local import transcribe
from app.teacher_openai import teacher_answer
from app.tts_local import speak
from app.voice_id import identify_speaker
from app.memory import get_student_memory, update_student_progress, build_memory_summary
from app.curriculum_retriever import pick_pack_id, retrieve_curriculum_chunks


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


def main() -> None:
    audio_path = find_audio_file()
    print(f"Using audio: {audio_path}")

    raw = identify_speaker(str(audio_path))
    print(f"Raw speaker match: {raw}")

    speaker = raw if raw else "Student"
    print(f"Detected speaker (final): {speaker}")
    STUDENT["name"] = speaker
    mem = get_student_memory(STUDENT["name"])
    STUDENT["memory_summary"] = build_memory_summary(mem)

    print(f"Detected speaker: {speaker}")
    STUDENT["name"] = speaker

    question = transcribe(str(audio_path))
    print("\n--- TRANSCRIBED QUESTION ---")
    print(question)

    pack_id = pick_pack_id(STUDENT)

    chunks = retrieve_curriculum_chunks(pack_id, question, top_k=4)
    curriculum_excerpts = "\n\n".join(
    [f"[{c['chunk_id']}]\n{c['text']}" for c in chunks]
    ) or "No matching curriculum excerpt found."


    answer = teacher_answer(question, STUDENT, curriculum_excerpts=curriculum_excerpts)

    topic_guess = STUDENT.get("subject")
    update_student_progress(
    name=STUDENT["name"],
    question=question,
    answer=answer,
    topic=topic_guess,
    )


    print("\n--- TEACHER ANSWER ---")
    print(answer)

    print("\n--- SPEAKING ANSWER ---")
    speak(answer)


if __name__ == "__main__":
    main()
