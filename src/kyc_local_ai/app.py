from __future__ import annotations

from time import time
from typing import Any

from flask import Flask, jsonify, request

from .config import load_settings
from .pipeline import analyze
from .schema import validate_payload

app = Flask(__name__)
settings = load_settings()
_rate_window: dict[str, list[float]] = {}


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
        "real_models_available": settings.real_models_available,
        "required_models": ["FACE_EMBEDDING_ONNX", "LIVENESS_ONNX"],
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
