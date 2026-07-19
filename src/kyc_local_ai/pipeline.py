from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from .config import Settings
from .decision_engine import decide
from .device_intelligence import evaluate_device
from .face import compare_document_face, embedding_hash
from .fraud_engine import evaluate_fraud
from .identity_graph import build_identity_graph
from .liveness import analyze_video_liveness
from .media import cleanup, fetch_file
from .media_probe import probe
from .model_registry import model_versions
from .ocr import analyze_document
from .workflow import StepTimer, event


def analyze(payload: dict[str, Any], settings: Settings) -> dict[str, Any]:
    started = time.time()
    timer = StepTimer()
    events: list[dict[str, Any]] = [event("kyc_started", request_id=payload.get("RequestID"))]
    paths: list[Path | None] = []
    try:
        with timer.measure("download_ms"):
            doc_front = fetch_file(payload.get("DocumentURL", ""), ".jpg")
            doc_back = fetch_file(payload.get("DocumentBackURL", ""), ".jpg")
            video = fetch_file(payload.get("FacialVideoURL", ""), ".mp4")
        paths = [doc_front, doc_back, video]
        events.append(event("media_received"))

        with timer.measure("media_probe_ms"):
            front_probe, front_flags = probe(doc_front, "image")
            back_probe, back_flags = probe(doc_back, "image")
            video_probe, video_flags = probe(video, "video")
        media_flags = front_flags + back_flags + video_flags

        with timer.measure("ocr_ms"):
            document_score, document_details = analyze_document(doc_front, doc_back)
        events.append(event("ocr_completed", score=document_score))

        with timer.measure("liveness_ms"):
            liveness_score, replay_risk, liveness_details, reference_frame = analyze_video_liveness(video)
        events.append(event("liveness_completed", score=liveness_score, replay_risk=replay_risk))

        with timer.measure("face_ms"):
            face_score, embedding, face_details = compare_document_face(reference_frame, settings.real_models_available)
        events.append(event("face_completed", score=face_score))
        current_embedding_hash = embedding_hash(embedding, settings.face_biometry_secret)

        with timer.measure("device_ms"):
            device_trust = evaluate_device(payload)

        flags: list[str] = list(media_flags)
        if not settings.real_models_available:
            flags.append("local_models_not_configured")
        flags.extend(document_details.get("flags", []))
        if liveness_score < settings.min_liveness_score:
            flags.append("liveness_below_threshold")
        if face_score < settings.min_face_score:
            flags.append("face_match_below_threshold")

        with timer.measure("fraud_ms"):
            risk_score, fraud_flags, fraud_details = evaluate_fraud(
                media_flags=media_flags,
                document_flags=document_details.get("flags", []),
                liveness_score=liveness_score,
                replay_risk=replay_risk,
                device_fingerprint=payload.get("DeviceFingerprint", ""),
                ip_address=payload.get("IPAddress", ""),
            )
        flags.extend(fraud_flags)
        if device_trust["risk"] == "HIGH":
            flags.append("device_high_risk")

        with timer.measure("scoring_ms"):
            final_score = round(
                document_score * 0.24
                + face_score * 0.28
                + liveness_score * 0.32
                + (100 - replay_risk) * 0.08
                + (100 - risk_score) * 0.04
                + device_trust["score"] * 0.04
            )
            final_score = max(0, min(final_score, 100))

        with timer.measure("decision_ms"):
            decision, reasons, rules = decide(
                settings=settings,
                score=final_score,
                document_score=document_score,
                face_score=face_score,
                liveness_score=liveness_score,
                replay_risk=replay_risk,
                risk_score=risk_score,
                models_available=settings.real_models_available,
                flags=sorted(set(flags)),
            )
        events.append(event("decision_completed", decision=decision, reasons=reasons))

        return {
            "provider": "chainfx_local_ai",
            "model_version": "chainfx-local-ai-service-v1",
            "provider_version": settings.provider_version,
            "model_versions": model_versions(settings),
            "decision": decision,
            "score": final_score,
            "document_score": document_score,
            "face_match_score": face_score,
            "liveness_score": liveness_score,
            "replay_risk_score": replay_risk,
            "duplicate_score": 100,
            "risk_score": risk_score,
            "latency_ms": int((time.time() - started) * 1000),
            "embedding": embedding,
            "embedding_hash": current_embedding_hash,
            "flags": sorted(set(flags)),
            "reasons": reasons,
            "details": {
                "self_hosted": True,
                "request_id": payload.get("RequestID"),
                "user_id": payload.get("UserID"),
                "settings": {
                    "real_models_available": settings.real_models_available,
                    "min_approval_score": settings.min_approval_score,
                    "min_face_score": settings.min_face_score,
                    "min_liveness_score": settings.min_liveness_score,
                },
                "workflow_events": events,
                "rules": rules,
                "timings_ms": timer.timings_ms,
                "media": {
                    "document_front": front_probe.as_dict() if front_probe else None,
                    "document_back": back_probe.as_dict() if back_probe else None,
                    "facial_video": video_probe.as_dict() if video_probe else None,
                },
                "document": document_details,
                "face": face_details,
                "liveness": liveness_details,
                "fraud": fraud_details,
                "device_trust": device_trust,
                "identity_graph": build_identity_graph(payload, current_embedding_hash),
                "duplicate_detection": {
                    "method": "external_vector_index_hook",
                    "top_k": 20,
                    "provider_persists_index": False,
                    "status": "pending_gateway_vector_search",
                },
                "required_models": ["FACE_EMBEDDING_ONNX", "LIVENESS_ONNX"],
            },
        }
    finally:
        cleanup(paths)
