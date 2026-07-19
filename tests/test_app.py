from __future__ import annotations

import unittest
from unittest.mock import patch

import kyc_local_ai.app as app_module
from kyc_local_ai.config import Settings


class AppContractTest(unittest.TestCase):
    def setUp(self) -> None:
        app_module._rate_window.clear()
        app_module.settings = Settings(
            host="127.0.0.1",
            port=9097,
            api_key="secret",
            face_biometry_secret="bio-secret",
            face_embedding_model="models/face.onnx",
            liveness_model="models/live.onnx",
            ocr_provider_url="",
            min_approval_score=88,
            min_face_score=86,
            min_liveness_score=82,
        )
        self.client = app_module.app.test_client()

    def test_health_reports_provider_and_model_state(self) -> None:
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["ok"])
        self.assertEqual(data["provider"], "chainfx_local_ai")
        self.assertTrue(data["real_models_available"])

    def test_analyze_requires_bearer_token_when_api_key_is_configured(self) -> None:
        response = self.client.post("/analyze", json={})

        self.assertEqual(response.status_code, 401)

    def test_analyze_returns_contract(self) -> None:
        expected = {
            "provider": "chainfx_local_ai",
            "model_version": "chainfx-local-ai-service-v1",
            "decision": "manual_review",
            "score": 80,
            "document_score": 90,
            "face_match_score": 86,
            "liveness_score": 82,
            "replay_risk_score": 10,
            "duplicate_score": 100,
            "risk_score": 10,
            "latency_ms": 12,
            "embedding": [0.1, -0.2],
            "embedding_hash": "hash",
            "flags": [],
            "reasons": [],
            "details": {"self_hosted": True},
        }
        with patch("kyc_local_ai.app.analyze", return_value=expected):
            response = self.client.post(
                "/analyze",
                headers={"Authorization": "Bearer secret"},
                json={"RequestID": "req-1"},
            )

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        for key in expected:
            self.assertIn(key, data)
        self.assertEqual(data["embedding"], [0.1, -0.2])
        self.assertEqual(response.headers.get("X-Request-ID"), "req-1")

    def test_analyze_rejects_invalid_schema(self) -> None:
        response = self.client.post(
            "/analyze",
            headers={"Authorization": "Bearer secret"},
            json={"Level": 99, "DocumentURL": "file:///tmp/front.jpg"},
        )

        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertEqual(data["error"], "invalid_payload")
        self.assertIn("Level_must_be_1_2_or_3", data["errors"])
        self.assertIn("DocumentURL_must_be_http_url", data["errors"])


if __name__ == "__main__":
    unittest.main()
