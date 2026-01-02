from openai import OpenAI
from app.config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)


def _teacher_style_rules() -> str:
    return """
STYLE (talk like a real UK classroom teacher):
- Use warm, encouraging language.
- Use the student name naturally.
- Praise effort: "Good question", "Well done", "You're thinking well".
- If the student is confused, simplify and use a different example.
- Keep it spoken, simple, and clear for text-to-speech.
- No markdown, no symbols like **, no bullet characters, no weird formatting.
- Short sentences are better than long sentences.
"""


def _lesson_context_text(plan: dict, cohort_state: dict, lesson: dict, step: dict) -> str:
    # Build a friendly “where we are” summary
    year = plan.get("year", "Year 7")
    subject = plan.get("subject", "Maths")
    term = plan.get("term", "this term")

    unit_idx = cohort_state.get("unit_idx", 0)
    lesson_idx = cohort_state.get("lesson_idx", 0)
    step_idx = cohort_state.get("step_idx", 0)

    unit = plan["units"][unit_idx]
    unit_title = unit.get("unit_title", f"Unit {unit_idx + 1}")
    lesson_title = lesson.get("lesson_title", f"Lesson {lesson_idx + 1}")

    objectives = lesson.get("objectives", [])
    obj_text = " ".join([f"Objective: {o}" for o in objectives[:3]])

    step_type = step.get("type", "explain")
    step_text = step.get("text", "")

    return f"""
CLASS CONTEXT:
- Year group: {year}
- Subject: {subject}
- Term: {term}
- Unit: {unit_title}
- Lesson: {lesson_title}
- We are currently on step {step_idx + 1} of the lesson.
{obj_text}

CURRENT STEP TYPE: {step_type}
CURRENT STEP CONTENT:
{step_text}
""".strip()


def teacher_welcome(student: dict, plan: dict, cohort_state: dict, lesson: dict) -> str:
    name = student.get("name", "Student")
    year = plan.get("year", "Year 7")
    subject = plan.get("subject", student.get("subject", "Maths"))
    term = plan.get("term", "this term")
    unit = plan["units"][cohort_state.get("unit_idx", 0)]
    unit_title = unit.get("unit_title", "our unit")
    lesson_title = lesson.get("lesson_title", "today's lesson")

    system = f"""
You are a classroom teacher.
Your task: welcome the student and tell them what we are learning today.

Student name: {name}

Context:
- Year: {year}
- Subject: {subject}
- Term: {term}
- Unit: {unit_title}
- Lesson: {lesson_title}

Rules:
1) Start with: "{name},"
2) Be friendly and teacher-like.
3) Mention term, unit, and lesson.
4) Keep it short (2 to 4 sentences).
{_teacher_style_rules()}
"""

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": system}],
        temperature=0.4,
    )
    return resp.choices[0].message.content.strip()


def teacher_teach_step(student: dict, plan: dict, cohort_state: dict, lesson: dict, step: dict) -> str:
    name = student.get("name", "Student")
    ctx = _lesson_context_text(plan, cohort_state, lesson, step)

    system = f"""
You are a classroom teacher teaching a lesson in order.

You MUST teach the CURRENT STEP only.
Do not jump ahead to future steps.
Do not introduce new topics outside the lesson context.

Rules:
1) Start with: "{name},"
2) Teach the step in a clear spoken way.
3) If the step is "check_question", ask ONLY that check question.
4) No markdown or symbols.
{_teacher_style_rules()}

{ctx}
"""

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": system}],
        temperature=0.3,
    )
    return resp.choices[0].message.content.strip()


def teacher_answer_question_and_resume(
    student: dict,
    plan: dict,
    cohort_state: dict,
    lesson: dict,
    step: dict,
    question: str,
) -> str:
    name = student.get("name", "Student")
    ctx = _lesson_context_text(plan, cohort_state, lesson, step)

    system = f"""
You are a classroom teacher.

A student asked a question while we are in the middle of a lesson.
Answer the question kindly, then return to the lesson.

Rules:
1) Start with: "{name},"
2) First say something encouraging like:
   "Good question" or "You're thinking well".
3) Answer in simple spoken language.
4) Use an example if needed.
5) Then end with a short transition sentence:
   "Now let's continue our lesson from where we stopped."
6) Do NOT teach the next step. Just resume verbally.
7) No markdown or symbols.
{_teacher_style_rules()}

{ctx}
"""

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": question},
        ],
        temperature=0.35,
    )
    return resp.choices[0].message.content.strip()
