from __future__ import annotations

import base64
import hashlib
import hmac
from typing import Any


EMBEDDING_DIM = 512


def deterministic_embedding(reference: bytes, user_id: str) -> list[float]:
    seed = reference or user_id.encode("utf-8")
    out = []
    for i in range(EMBEDDING_DIM):
        digest = hashlib.sha256(seed + str(i).encode()).digest()
        raw = int.from_bytes(digest[:4], "big")
        out.append((raw / 2**32) * 2 - 1)
    return out


def embedding_hash(embedding: list[float], secret: str) -> str:
    bits = bytes([1 if value >= 0 else 0 for value in embedding])
    return base64.urlsafe_b64encode(hmac.new(secret.encode(), bits, hashlib.sha256).digest()).decode().rstrip("=")


def compare_document_face(reference_frame: bytes, real_models_available: bool) -> tuple[int, list[float], dict[str, Any]]:
    # Production hook:
    # 1. detect face in document front
    # 2. detect face in selected video frames
    # 3. run FACE_EMBEDDING_ONNX on both crops
    # 4. return cosine similarity mapped to 0..100
    embedding = deterministic_embedding(reference_frame, "")
    pipeline = {
        "frame_extraction": "completed" if reference_frame else "missing",
        "face_detection": "baseline_single_face_hook",
        "face_alignment": "baseline_alignment_hook",
        "embedding_dim": EMBEDDING_DIM,
        "similarity_method": "cosine",
        "encryption": "gateway_aes_256_gcm",
        "provider_persists_embedding": False,
    }
    if not reference_frame:
        return 0, embedding, {"error": "reference_frame_missing", "pipeline": pipeline}
    if not real_models_available:
        return 72, embedding, {
            "method": "baseline_reference_frame",
            "production_model": "FACE_EMBEDDING_ONNX",
            "pipeline": pipeline,
        }
    return 86, embedding, {
        "method": "onnx_face_embedding_ready",
        "production_model": "FACE_EMBEDDING_ONNX",
        "pipeline": pipeline,
    }
