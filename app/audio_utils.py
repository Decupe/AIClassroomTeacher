import subprocess
import numpy as np
import torch

def load_audio_ffmpeg(path: str, sr: int = 16000) -> torch.Tensor:
    """
    Load audio using ffmpeg into a mono float32 waveform tensor [1, T] at sr Hz.
    Requires ffmpeg in PATH (or set PATH in session).
    """
    cmd = [
        "ffmpeg",
        "-i", path,
        "-f", "f32le",
        "-acodec", "pcm_f32le",
        "-ac", "1",
        "-ar", str(sr),
        "-hide_banner",
        "-loglevel", "error",
        "pipe:1",
    ]
    out = subprocess.check_output(cmd)
    wav = np.frombuffer(out, dtype=np.float32).copy()

    return torch.from_numpy(wav).unsqueeze(0)  # [1, T]
