import re
import pyttsx3

_engine = pyttsx3.init()

def _sanitize_for_speech(text: str) -> str:
    # Remove Markdown bold/italics markers like **text** or *text*
    text = text.replace("**", "").replace("*", "")

    # Replace common fractions so it sounds natural
    # e.g., 1/4 -> "one quarter"
    fraction_map = {
        "1/2": "one half",
        "1/3": "one third",
        "2/3": "two thirds",
        "1/4": "one quarter",
        "3/4": "three quarters",
        "1/5": "one fifth",
        "1/6": "one sixth",
        "1/8": "one eighth",
        "3/8": "three eighths",
    }
    for k, v in fraction_map.items():
        text = text.replace(k, v)

    # Replace bullet symbols that some engines read weirdly
    text = text.replace("•", "").replace("-", "")

    # Collapse excessive whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text

def speak(text: str) -> None:
    """
    Speak text aloud using the system's offline TTS engine.
    """
    clean = _sanitize_for_speech(text)
    _engine.say(clean)
    _engine.runAndWait()

