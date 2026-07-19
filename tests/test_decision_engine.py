from __future__ import annotations

import unittest

from kyc_local_ai.config import Settings
from kyc_local_ai.decision_engine import decide


def settings() -> Settings:
    return Settings(
        host="127.0.0.1",
        port=9097,
        api_key="secret",
        face_biometry_secret="bio",
        face_embedding_model="models/face.onnx",
        liveness_model="models/live.onnx",
        ocr_provider_url="",
        min_approval_score=88,
        min_face_score=86,
        min_liveness_score=82,
    )


class DecisionEngineTest(unittest.TestCase):
    def test_duplicate_or_fraud_flag_forces_manual_review(self) -> None:
        decision, reasons, rules = decide(
            settings=settings(),
            score=95,
            document_score=95,
            face_score=95,
            liveness_score=95,
            replay_risk=5,
            risk_score=5,
            models_available=True,
            flags=["same_face_seen_on_other_account"],
        )

        self.assertEqual(decision, "manual_review")
        self.assertIn("same_face_seen_on_other_account", reasons)
        self.assertTrue(any(rule["id"] == "final_score" for rule in rules))


if __name__ == "__main__":
    unittest.main()
