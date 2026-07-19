from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import cv2
except Exception:
    cv2 = None

try:
    import numpy as np
except Exception:
    np = None


def analyze_video_liveness(path: Path | None) -> tuple[int, int, dict[str, Any], bytes]:
    if path is None:
        return 0, 100, {"error": "video_missing"}, b""
    if cv2 is None or np is None:
        return 0, 100, {"error": "opencv_or_numpy_unavailable"}, b""

    cap = cv2.VideoCapture(str(path))
    frames = []
    for _ in range(40):
        ok, frame = cap.read()
        if not ok:
            break
        frames.append(frame)
    cap.release()

    if len(frames) < 8:
        return 20, 80, {"frames": len(frames), "error": "insufficient_frames"}, b""

    diffs = []
    prev = cv2.cvtColor(frames[0], cv2.COLOR_BGR2GRAY)
    for frame in frames[1:]:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        diffs.append(float(np.mean(cv2.absdiff(prev, gray))))
        prev = gray

    avg_motion = sum(diffs) / len(diffs)
    motion_score = max(0, min(int(avg_motion * 7), 100))
    replay_risk = max(0, min(100 - motion_score, 100))
    _, encoded = cv2.imencode(".jpg", frames[len(frames) // 2])
    modules = {
        "motion": {"score": motion_score, "status": "PASS" if motion_score >= 60 else "REVIEW"},
        "blink": {"score": 0, "status": "MODEL_REQUIRED"},
        "head_pose": {"score": 0, "status": "MODEL_REQUIRED"},
        "replay": {"score": 100 - replay_risk, "status": "PASS" if replay_risk < 70 else "FAIL"},
        "screen": {"score": 0, "status": "MODEL_REQUIRED"},
        "print": {"score": 0, "status": "MODEL_REQUIRED"},
        "texture": {"score": 0, "status": "MODEL_REQUIRED"},
        "reflection": {"score": 0, "status": "MODEL_REQUIRED"},
        "depth": {"score": 0, "status": "MODEL_REQUIRED"},
        "challenge": {"score": 0, "status": "MODEL_REQUIRED"},
    }

    return motion_score, replay_risk, {
        "frames": len(frames),
        "avg_motion": avg_motion,
        "method": "motion_baseline",
        "production_model": "LIVENESS_ONNX",
        "modules": modules,
    }, encoded.tobytes()
