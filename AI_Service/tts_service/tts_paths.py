"""Đường dẫn thư mục model (checkpoint XTTS / viXTTS)."""
from __future__ import annotations

import os
from pathlib import Path

_SERVICE_DIR = Path(__file__).resolve().parent


def model_dir_str() -> str:
    """
    Thư mục chứa model.pth, config.json, vocab.json.
    Mặc định: thư mục model/ cạnh tts_service (không phụ thuộc cwd).

    Đổi checkpoint (vd viXTTS): TTS_MODEL_DIR=model_vixtts
    (tương đối thư mục tts_service) hoặc đường dẫn tuyệt đối.
    """
    raw = (os.environ.get("TTS_MODEL_DIR") or "model").strip() or "model"
    p = Path(raw)
    full = p.resolve() if p.is_absolute() else (_SERVICE_DIR / p).resolve()
    return str(full).replace("\\", "/").rstrip("/") + "/"
