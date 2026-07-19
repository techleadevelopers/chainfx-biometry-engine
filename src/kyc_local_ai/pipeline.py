from __future__ import annotations

import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .config import Settings
from .face import compare_document_face, embedding_hash
from .liveness import analyze_video_liveness
from .media import cleanup, fetch_file
from .ocr import analyze_document


def analyze(payload: dict[str, Any], settings: Settings) -> dict[str, Any]:
    started = time.time()
    paths: list[Path | None] = []
    try:
        doc_front = fetch_file(payload.get("DocumentURL", ""), ".jpg")
        doc_back = fetch_file(payload.get("DocumentBackURL", ""), ".jpg")
        video = fetch_file(payload.get("FacialVideoURL", ""), ".mp4")
        paths = [doc_front, doc_back, video]

        document_score, document_details = analyze_document(doc_front, doc_back)
        liveness_score, replay_risk, liveness_details, reference_frame = analyze_video_liveness(video)
        face_score, embedding, face_details = compare_document_face(reference_frame, settings.real_models_available)

        flags: list[str] = []
        if not settings.real_models_available:
            flags.append("local_models_not_configured")
        flags.extend(document_details.get("flags", []))
        if liveness_score < settings.min_liveness_score:
            flags.append("liveness_below_threshold")
        if face_score < settings.min_face_score:
            flags.append("face_match_below_threshold")

        final_score = round(
            document_score * 0.25
            + face_score * 0.30
            + liveness_score * 0.35
            + (100 - replay_risk) * 0.10
        )

        decision = "manual_review"
        if settings.real_models_available and final_score >= settings.min_approval_score and not flags:
            decision = "approved"
        if final_score < 55 or face_score < 40 or liveness_score < 35:
            decision = "rejected"

        return {
            "provider": "chainfx_local_ai",
            "model_version": "chainfx-local-ai-service-v1",
            "decision": decision,
            "score": max(0, min(final_score, 100)),
            "document_score": document_score,
            "face_match_score": face_score,
            "liveness_score": liveness_score,
            "replay_risk_score": replay_risk,
            "duplicate_score": 100,
            "risk_score": 10,
            "latency_ms": int((time.time() - started) * 1000),
            "embedding": embedding,
            "embedding_hash": embedding_hash(embedding, settings.face_biometry_secret),
            "flags": flags,
            "details": {
                "self_hosted": True,
                "settings": {
                    "real_models_available": settings.real_models_available,
                    "min_approval_score": settings.min_approval_score,
                    "min_face_score": settings.min_face_score,
                    "min_liveness_score": settings.min_liveness_score,
                },
                "document": document_details,
                "face": face_details,
                "liveness": liveness_details,
                "required_models": ["FACE_EMBEDDING_ONNX", "LIVENESS_ONNX"],
            },
        }
    finally:
        cleanup(paths)
