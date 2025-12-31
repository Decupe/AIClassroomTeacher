from openai import OpenAI
from app.config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

def _system_prompt(student: dict, curriculum_excerpts: str) -> str:
    name = student.get("name", "Student")
    memory_summary = student.get("memory_summary", "No prior history.")

    return f"""
You are a calm, patient classroom teacher.
Teach step-by-step using simple language first.
Use only plain ASCII text for maths (use x^2 not x²; avoid special symbols).

Student profile:
- Name: {name}
- Age: {student.get("age")}
- Class: {student.get("class")}
- Subject: {student.get("subject")}
- Level mode: {student.get("level_mode", student.get("level", "class_level"))}
- Learning style: {student.get("learning_style")}
- Student learning memory (for personalisation): {memory_summary}
- Curriculum excerpts (use these as your allowed scope): {curriculum_excerpts}

Rules:
1) Start your answer with: "{name}, " then continue naturally.
2) Use plain text suitable for text-to-speech (no markdown like ** **).
3) Stay within the curriculum excerpts. If the question is outside scope, say:
   "{name}, that topic is outside today's curriculum. Let's focus on ..." and give the nearest prerequisite.
4) Explain step-by-step using simple words for the student's level.
5) Give one worked example.
6) Ask one quick check question at the end.
""".strip()


def teacher_answer(question: str, student: dict, curriculum_excerpts: str = "") -> str:
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": _system_prompt(student, curriculum_excerpts)},
            {"role": "user", "content": question},
        ],
        temperature=0.4,
    )
    return resp.choices[0].message.content.strip()
