from __future__ import annotations

from typing import Any


def evaluate_fraud(
    *,
    media_flags: list[str],
    document_flags: list[str],
    liveness_score: int,
    replay_risk: int,
    device_fingerprint: str,
    ip_address: str,
) -> tuple[int, list[str], dict[str, Any]]:
    flags: list[str] = []
    flags.extend(media_flags)

    if not device_fingerprint:
        flags.append("device_fingerprint_missing")
    if not ip_address:
        flags.append("ip_missing")
    if replay_risk >= 70:
        flags.append("high_replay_risk")
    if liveness_score < 50:
        flags.append("weak_liveness")
    flags.extend(document_flags)

    penalty = 0
    for flag in flags:
        if flag in {"video_too_long", "invalid_video_mime", "high_replay_risk"}:
            penalty += 25
        elif flag.endswith("_missing"):
            penalty += 18
        else:
            penalty += 8

    risk_score = max(0, min(penalty, 100))
    return risk_score, sorted(set(flags)), {
        "risk_score": risk_score,
        "signals": sorted(set(flags)),
    }
