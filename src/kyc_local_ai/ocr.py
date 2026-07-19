from __future__ import annotations

from pathlib import Path
from typing import Any

from .quality import image_quality


def analyze_document(front: Path | None, back: Path | None) -> tuple[int, dict[str, Any]]:
    front_score, front_details = image_quality(front)
    back_score, back_details = image_quality(back)
    score = int(front_score * 0.65 + back_score * 0.35)
    flags = []
    if front_score < 70:
        flags.append("front_quality_low")
    if back_score < 70:
        flags.append("back_quality_low")
    return score, {
        "method": "quality_and_ocr_hook",
        "production_model": "OCR_PROVIDER_URL_or_local_ocr",
        "front": front_details,
        "back": back_details,
        "flags": flags,
    }
