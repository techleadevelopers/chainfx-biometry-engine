from __future__ import annotations

from typing import Any

from .config import Settings


def model_versions(settings: Settings) -> dict[str, str]:
    return {
        "face_embedding": settings.face_model_version,
        "liveness": settings.liveness_model_version,
        "ocr": settings.ocr_model_version,
        "fraud": settings.fraud_model_version,
    }


def registry(settings: Settings) -> dict[str, Any]:
    return {
        "provider": "chainfx_local_ai",
        "provider_version": settings.provider_version,
        "model_versions": model_versions(settings),
        "real_models_available": settings.real_models_available,
        "models": {
            "face_embedding": {
                "version": settings.face_model_version,
                "path": settings.face_embedding_model,
                "embedding_dim": 512,
                "similarity": "cosine",
                "configured": bool(settings.face_embedding_model),
            },
            "liveness": {
                "version": settings.liveness_model_version,
                "path": settings.liveness_model,
                "modules": ["motion", "blink", "head_pose", "replay", "screen", "print", "texture", "reflection", "depth", "challenge"],
                "configured": bool(settings.liveness_model),
            },
            "ocr": {
                "version": settings.ocr_model_version,
                "provider_url": settings.ocr_provider_url,
                "fields": ["name", "cpf", "birth_date", "document_number", "issuer", "issue_date", "expiry_date"],
            },
            "fraud": {
                "version": settings.fraud_model_version,
                "modules": ["device_intelligence", "duplicate_detection", "identity_graph", "risk_scoring"],
            },
        },
    }
