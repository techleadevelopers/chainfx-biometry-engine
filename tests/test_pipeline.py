from __future__ import annotations

import unittest
from unittest.mock import patch

from kyc_local_ai.config import Settings
from kyc_local_ai.pipeline import analyze


def settings(real_models: bool) -> Settings:
    return Settings(
        host="127.0.0.1",
        port=9097,
        api_key="test-key",
        face_biometry_secret="test-biometry-secret",
        face_embedding_model="models/face.onnx" if real_models else "",
        liveness_model="models/live.onnx" if real_models else "",
        ocr_provider_url="",
        min_approval_score=88,
        min_face_score=86,
        min_liveness_score=82,
    )


class PipelineTest(unittest.TestCase):
    def clean_probe(self, *_args):
        return None, []

    def test_no_real_models_never_approves_and_returns_embedding(self) -> None:
        with patch("kyc_local_ai.pipeline.fetch_file", return_value=None), \
             patch("kyc_local_ai.pipeline.probe", side_effect=self.clean_probe), \
             patch("kyc_local_ai.pipeline.analyze_document", return_value=(96, {"flags": []})), \
             patch("kyc_local_ai.pipeline.analyze_video_liveness", return_value=(94, 3, {"method": "test"}, b"frame")), \
             patch("kyc_local_ai.pipeline.compare_document_face", return_value=(92, [0.1, -0.2, 0.3], {"method": "test"})):
            result = analyze({
                "DocumentURL": "https://cdn/front.jpg",
                "DocumentBackURL": "https://cdn/back.jpg",
                "FacialVideoURL": "https://cdn/video.mp4",
                "UserID": "user-1",
            }, settings(real_models=False))

        self.assertEqual(result["decision"], "manual_review")
        self.assertIn("local_models_not_configured", result["flags"])
        self.assertEqual(result["provider"], "chainfx_local_ai")
        self.assertIsInstance(result["embedding"], list)
        self.assertGreater(len(result["embedding"]), 0)
        self.assertIsInstance(result["embedding_hash"], str)
        self.assertNotEqual(result["embedding_hash"], "")
        self.assertIn("rules", result["details"])
        self.assertIn("timings_ms", result["details"])
        self.assertIn("workflow_events", result["details"])
        self.assertIn("media", result["details"])
        self.assertIn("reasons", result)

    def test_real_models_can_approve_when_scores_are_high_and_no_flags(self) -> None:
        with patch("kyc_local_ai.pipeline.fetch_file", return_value=None), \
             patch("kyc_local_ai.pipeline.probe", side_effect=self.clean_probe), \
             patch("kyc_local_ai.pipeline.analyze_document", return_value=(98, {"flags": []})), \
             patch("kyc_local_ai.pipeline.analyze_video_liveness", return_value=(96, 2, {"method": "test"}, b"frame")), \
             patch("kyc_local_ai.pipeline.compare_document_face", return_value=(95, [0.4, 0.2, -0.1], {"method": "onnx"})):
            result = analyze({"DeviceFingerprint": "device-ok", "IPAddress": "127.0.0.1"}, settings(real_models=True))

        self.assertEqual(result["decision"], "approved")
        self.assertGreaterEqual(result["score"], 88)
        self.assertEqual(result["flags"], [])
        self.assertTrue(result["details"]["settings"]["real_models_available"])
        self.assertEqual(result["reasons"], [])

    def test_low_liveness_rejects(self) -> None:
        with patch("kyc_local_ai.pipeline.fetch_file", return_value=None), \
             patch("kyc_local_ai.pipeline.probe", side_effect=self.clean_probe), \
             patch("kyc_local_ai.pipeline.analyze_document", return_value=(90, {"flags": []})), \
             patch("kyc_local_ai.pipeline.analyze_video_liveness", return_value=(20, 90, {"method": "test"}, b"frame")), \
             patch("kyc_local_ai.pipeline.compare_document_face", return_value=(90, [0.1, 0.2], {"method": "test"})):
            result = analyze({}, settings(real_models=True))

        self.assertEqual(result["decision"], "rejected")
        self.assertIn("liveness_below_threshold", result["flags"])
        self.assertIn("liveness", result["reasons"])

    def test_low_face_match_rejects(self) -> None:
        with patch("kyc_local_ai.pipeline.fetch_file", return_value=None), \
             patch("kyc_local_ai.pipeline.probe", side_effect=self.clean_probe), \
             patch("kyc_local_ai.pipeline.analyze_document", return_value=(90, {"flags": []})), \
             patch("kyc_local_ai.pipeline.analyze_video_liveness", return_value=(95, 4, {"method": "test"}, b"frame")), \
             patch("kyc_local_ai.pipeline.compare_document_face", return_value=(25, [0.1, 0.2], {"method": "test"})):
            result = analyze({}, settings(real_models=True))

        self.assertEqual(result["decision"], "rejected")
        self.assertIn("face_match_below_threshold", result["flags"])
        self.assertIn("face_similarity", result["reasons"])


if __name__ == "__main__":
    unittest.main()
