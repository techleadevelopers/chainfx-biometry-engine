from __future__ import annotations

from time import time
from typing import Any

from flask import Flask, jsonify, request

from .config import load_settings
from .metrics import metrics
from .model_registry import registry
from .pipeline import analyze
from .schema import validate_payload

app = Flask(__name__)
settings = load_settings()
_rate_window: dict[str, list[float]] = {}
_review_cache: dict[str, dict[str, Any]] = {}


def require_auth() -> tuple[bool, Any]:
    if not settings.api_key:
        return True, None
    got = request.headers.get("Authorization", "")
    if got != f"Bearer {settings.api_key}":
        return False, (jsonify({"error": "unauthorized"}), 401)
    return True, None


def request_identity() -> str:
    return request.headers.get("X-Forwarded-For", request.remote_addr or "unknown").split(",", 1)[0].strip()


def rate_limit() -> tuple[bool, Any]:
    key = request_identity()
    now = time()
    window = [item for item in _rate_window.get(key, []) if now - item < 60]
    if len(window) >= 60:
        return False, (jsonify({"error": "rate_limited", "request_id": request.headers.get("X-Request-ID", "")}), 429)
    window.append(now)
    _rate_window[key] = window
    return True, None


@app.get("/health")
def health() -> Any:
    return jsonify({
        "ok": True,
        "provider": "chainfx_local_ai",
        "provider_version": settings.provider_version,
        "real_models_available": settings.real_models_available,
        "required_models": ["FACE_EMBEDDING_ONNX", "LIVENESS_ONNX"],
    })


@app.get("/models")
def models() -> Any:
    return jsonify(registry(settings))


@app.get("/metrics")
def prometheus_metrics() -> Any:
    return app.response_class(metrics.prometheus(), mimetype="text/plain; version=0.0.4")


@app.get("/review/<request_id>")
def review(request_id: str) -> Any:
    ok, error = require_auth()
    if not ok:
        return error
    result = _review_cache.get(request_id)
    if not result:
        return jsonify({"error": "review_not_found", "request_id": request_id}), 404
    return jsonify({
        "request_id": request_id,
        "provider": result.get("provider"),
        "provider_version": result.get("provider_version"),
        "model_versions": result.get("model_versions"),
        "decision": result.get("decision"),
        "score": result.get("score"),
        "reasons": result.get("reasons", []),
        "flags": result.get("flags", []),
        "document": result.get("details", {}).get("document"),
        "face": result.get("details", {}).get("face"),
        "liveness": result.get("details", {}).get("liveness"),
        "rules": result.get("details", {}).get("rules", []),
        "timings_ms": result.get("details", {}).get("timings_ms", {}),
        "media": result.get("details", {}).get("media", {}),
        "device_trust": result.get("details", {}).get("device_trust", {}),
        "identity_graph": result.get("details", {}).get("identity_graph", {}),
    })


@app.post("/analyze")
def analyze_route() -> Any:
    ok, error = require_auth()
    if not ok:
        return error
    ok, error = rate_limit()
    if not ok:
        return error
    payload = request.get_json(force=True)
    valid, errors = validate_payload(payload)
    if not valid:
        return jsonify({
            "error": "invalid_payload",
            "errors": errors,
            "request_id": request.headers.get("X-Request-ID", payload.get("RequestID", "") if isinstance(payload, dict) else ""),
        }), 400
    payload.setdefault("RequestID", request.headers.get("X-Request-ID", ""))
    payload.setdefault("IPAddress", request_identity())
    result = analyze(payload, settings)
    metrics.record(result)
    if payload.get("RequestID"):
        _review_cache[payload["RequestID"]] = result
        if len(_review_cache) > 500:
            oldest_key = next(iter(_review_cache))
            _review_cache.pop(oldest_key, None)
    response = jsonify(result)
    if payload.get("RequestID"):
        response.headers["X-Request-ID"] = payload["RequestID"]
    if request.headers.get("X-Correlation-ID"):
        response.headers["X-Correlation-ID"] = request.headers["X-Correlation-ID"]
    return response


def main() -> None:
    app.run(host=settings.host, port=settings.port)


if __name__ == "__main__":
    main()
