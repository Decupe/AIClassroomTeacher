import whisper

# Load once (faster for repeated runs)
_MODEL = whisper.load_model("base")  # try "small" for better accuracy

def transcribe(audio_path: str) -> str:
    """
    Transcribe an audio file to text using local Whisper.
    """
    result = _MODEL.transcribe(audio_path)
    return (result.get("text") or "").strip()
