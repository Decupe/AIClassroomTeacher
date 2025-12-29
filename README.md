# AI Classroom Teacher (Voice → Teacher Tutor)

A voice-driven classroom tutor prototype that:
- transcribes a student question from audio (local Whisper),
- identifies the student by voice (speaker embeddings),
- generates a calm, step-by-step “teacher-style” answer (OpenAI),
- speaks the answer back (local TTS).

This project is built as an MVP to explore personalised, always-available classroom teaching support.

## Key Features
- **Local Speech-to-Text (Whisper):** transcribes student questions from audio files.
- **Voice ID (Speaker Recognition):** register a student voice and recognise them later.
- **Personalised Teaching:** injects student profile into the prompt and greets by name.
- **Text-to-Speech:** reads the teacher answer aloud (TTS-friendly formatting).

## Architecture (MVP)
`Audio (student) → STT (Whisper) → Speaker ID → Prompt (student profile) → LLM → TTS`

## Project Structure
ai-classroom-teacher/
├─ app/
│ ├─ config.py
│ ├─ stt_local.py
│ ├─ teacher_openai.py
│ ├─ tts_local.py
│ ├─ audio_utils.py
│ ├─ voice_id.py
│ ├─ register_student.py
│ └─ run_demo.py
├─ samples/
│ ├─ student_question.(wav|m4a|mp3)
│ └─ samuel_register.m4a
├─ data/ # local-only (voice_db.json, progress later)
├─ .env # local-only (API key)
├─ .gitignore
└─ requirements.txt
