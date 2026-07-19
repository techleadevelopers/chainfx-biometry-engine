from __future__ import annotations

from pathlib import Path
from typing import Any

from .quality import image_quality


def empty_field(name: str) -> dict[str, Any]:
    return {"value": "", "confidence": 0.0, "field": name, "valid": False, "reason": "ocr_model_not_connected"}


def analyze_document(front: Path | None, back: Path | None) -> tuple[int, dict[str, Any]]:
    front_score, front_details = image_quality(front)
    back_score, back_details = image_quality(back)
    score = int(front_score * 0.65 + back_score * 0.35)
    flags = []
    if front_score < 70:
        flags.append("front_quality_low")
    if back_score < 70:
        flags.append("back_quality_low")
    # Production hook: replace these empty fields with PaddleOCR/local OCR output.
    structured = {
        "name": empty_field("name"),
        "cpf": empty_field("cpf"),
        "birth_date": empty_field("birth_date"),
        "document_number": empty_field("document_number"),
        "issuer": empty_field("issuer"),
        "issue_date": empty_field("issue_date"),
        "expiry_date": empty_field("expiry_date"),
    }

    return score, {
        "method": "quality_and_ocr_hook",
        "production_model": "PADDLEOCR_OR_LOCAL_OCR",
        "ocr": structured,
        "normalization": {
            "cpf_check_digits": "pending_model_output",
            "name_invalid_characters": "pending_model_output",
            "date_coherence": "pending_model_output",
            "document_expired": "pending_model_output",
        },
        "cross_validation": {
            "cpf_matches_user": "pending_gateway_context",
            "name_matches_user": "pending_gateway_context",
            "birth_date_matches_user": "pending_gateway_context",
        },
        "front": front_details,
        "back": back_details,
        "flags": flags,
    }
