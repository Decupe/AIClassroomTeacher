import re
import subprocess
import time


def _clean_for_tts(text: str) -> str:
    # Remove markdown-like artifacts and weird chars
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = text.replace("Â", "")
    text = text.replace("²", " squared ")
    text = text.replace("/", " over ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _chunk_text(text: str, max_len: int = 700) -> list[str]:
    # Bigger chunks = smoother (fewer starts/stops)
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks, buf = [], ""
    for s in sentences:
        if not s:
            continue
        if len(buf) + len(s) + 1 <= max_len:
            buf = (buf + " " + s).strip()
        else:
            if buf:
                chunks.append(buf)
            buf = s.strip()
    if buf:
        chunks.append(buf)
    return chunks


def speak(text: str) -> None:
    text = _clean_for_tts(text)
    if not text:
        return

    chunks = _chunk_text(text, max_len=700)

    for i, chunk in enumerate(chunks, start=1):
        print(f"[TTS] PS chunk {i}/{len(chunks)}: {chunk[:60]}...")
        safe = chunk.replace('"', "'")

        ps = (
            "Add-Type -AssemblyName System.Speech; "
            "$speak = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            "$speak.Rate = 0; "
            f'$speak.Speak("{safe}");'
        )

        subprocess.run(["powershell", "-Command", ps], check=False)
        time.sleep(0.1)
