from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    host: str
    port: int
    api_key: str
    face_biometry_secret: str
    face_embedding_model: str
    liveness_model: str
    ocr_provider_url: str
    min_approval_score: int
    min_face_score: int
    min_liveness_score: int
    provider_version: str = "2.4.1"
    face_model_version: str = "arcface-local-v1"
    liveness_model_version: str = "chainfx-liveness-v1"
    ocr_model_version: str = "local-ocr-v1"
    fraud_model_version: str = "fraud-engine-v3"

    @property
    def real_models_available(self) -> bool:
        return bool(self.face_embedding_model and self.liveness_model)


def load_settings() -> Settings:
    return Settings(
        host=os.getenv("KYC_PROVIDER_HOST", "127.0.0.1"),
        port=int(os.getenv("KYC_PROVIDER_PORT", "9097")),
        api_key=os.getenv("KYC_PROVIDER_API_KEY", "").strip(),
        face_biometry_secret=os.getenv("FACE_BIOMETRY_SECRET", os.getenv("KYC_PROVIDER_API_KEY", "local-dev")),
        face_embedding_model=os.getenv("FACE_EMBEDDING_ONNX", "").strip(),
        liveness_model=os.getenv("LIVENESS_ONNX", "").strip(),
        ocr_provider_url=os.getenv("OCR_PROVIDER_URL", "").strip(),
        min_approval_score=int(os.getenv("KYC_MIN_APPROVAL_SCORE", "88")),
        min_face_score=int(os.getenv("KYC_MIN_FACE_SCORE", "86")),
        min_liveness_score=int(os.getenv("KYC_MIN_LIVENESS_SCORE", "82")),
        provider_version=os.getenv("KYC_PROVIDER_VERSION", "2.4.1").strip(),
        face_model_version=os.getenv("KYC_FACE_MODEL_VERSION", "arcface-local-v1").strip(),
        liveness_model_version=os.getenv("KYC_LIVENESS_MODEL_VERSION", "chainfx-liveness-v1").strip(),
        ocr_model_version=os.getenv("KYC_OCR_MODEL_VERSION", "local-ocr-v1").strip(),
        fraud_model_version=os.getenv("KYC_FRAUD_MODEL_VERSION", "fraud-engine-v3").strip(),
    )
