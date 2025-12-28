from openai import OpenAI
from app.config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)


def _system_prompt(student: dict) -> str:
    name = student.get("name", "Student")
    return f"""
You are a calm, patient classroom teacher.
Teach step-by-step using simple language first.
If the student is confused, simplify further and use a different example.

Student profile:
- Name: {name}
- Age: {student.get("age")}
- Class: {student.get("class")}
- Subject: {student.get("subject")}
- Level: {student.get("level")}
- Learning style: {student.get("learning_style")}

Rules:
1) Start your answer with: "{name}, " then continue naturally.
2) Use plain text suitable for text-to-speech (no markdown like ** **).
3) Explain step-by-step using simple words for the student's level.
4) Give one worked example.
5) Ask one quick check question at the end.
""".strip()


def teacher_answer(question: str, student: dict) -> str:
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": _system_prompt(student)},
            {"role": "user", "content": question},
        ],
        temperature=0.4,
    )
    return resp.choices[0].message.content.strip()
