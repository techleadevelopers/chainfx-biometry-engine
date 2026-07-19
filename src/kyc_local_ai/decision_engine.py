from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .config import Settings


@dataclass
class RuleResult:
    id: str
    status: str
    reason: str
    value: Any = None

    def as_dict(self) -> dict[str, Any]:
        return {"id": self.id, "status": self.status, "reason": self.reason, "value": self.value}


def decide(
    *,
    settings: Settings,
    score: int,
    document_score: int,
    face_score: int,
    liveness_score: int,
    replay_risk: int,
    risk_score: int,
    models_available: bool,
    flags: list[str],
) -> tuple[str, list[str], list[dict[str, Any]]]:
    rules = [
        RuleResult("document_quality", "pass" if document_score >= 70 else "fail", "document quality threshold", document_score),
        RuleResult("face_similarity", "pass" if face_score >= settings.min_face_score else "fail", "face match threshold", face_score),
        RuleResult("liveness", "pass" if liveness_score >= settings.min_liveness_score else "fail", "liveness threshold", liveness_score),
        RuleResult("replay_risk", "pass" if replay_risk < 70 else "fail", "replay risk threshold", replay_risk),
        RuleResult("fraud_risk", "pass" if risk_score < 70 else "fail", "fraud risk threshold", risk_score),
        RuleResult("models_available", "pass" if models_available else "review", "local ONNX models configured", models_available),
        RuleResult("final_score", "pass" if score >= settings.min_approval_score else "review", "approval score threshold", score),
    ]

    reasons: list[str] = []
    if any(rule.status == "fail" for rule in rules):
        decision = "rejected"
        reasons = [rule.id for rule in rules if rule.status == "fail"]
    elif any(rule.status == "review" for rule in rules) or flags:
        decision = "manual_review"
        reasons = [rule.id for rule in rules if rule.status == "review"] + flags
    else:
        decision = "approved"

    return decision, sorted(set(reasons)), [rule.as_dict() for rule in rules]
