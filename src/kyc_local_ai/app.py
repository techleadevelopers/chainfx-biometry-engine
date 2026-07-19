from __future__ import annotations

from typing import Any

from flask import Flask, jsonify, request

from .config import load_settings
from .pipeline import analyze

app = Flask(__name__)
settings = load_settings()


def require_auth() -> tuple[bool, Any]:
    if not settings.api_key:
        return True, None
    got = request.headers.get("Authorization", "")
    if got != f"Bearer {settings.api_key}":
        return False, (jsonify({"error": "unauthorized"}), 401)
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
    return jsonify(analyze(request.get_json(force=True), settings))


def main() -> None:
    app.run(host=settings.host, port=settings.port)


if __name__ == "__main__":
    main()
