"""
Compatibility shim for TorchAudio 2.9+ where torchaudio.list_audio_backends() was removed.
SpeechBrain 1.0.x still expects it during import.
"""

import torchaudio

# In torchaudio 2.9, list_audio_backends() is removed, but the internal backend
# helper may still exist (deprecated). We provide the missing attribute.
if not hasattr(torchaudio, "list_audio_backends"):
    backend = getattr(torchaudio, "_backend", None)
    if backend is not None and hasattr(backend, "list_audio_backends"):
        torchaudio.list_audio_backends = backend.list_audio_backends  # type: ignore[attr-defined]
