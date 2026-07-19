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


def image_quality(path: Path | None) -> tuple[int, dict[str, Any]]:
    if path is None:
        return 0, {"error": "missing_image"}
    if cv2 is None or np is None:
        return 0, {"error": "opencv_or_numpy_unavailable"}

    image = cv2.imread(str(path))
    if image is None:
        return 0, {"error": "image_decode_failed"}

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    brightness = float(np.mean(gray))
    height, width = image.shape[:2]

    score = 35
    if sharpness > 80:
        score += 30
    elif sharpness > 40:
        score += 15
    if 55 <= brightness <= 205:
        score += 20
    if min(height, width) >= 600:
        score += 15

    return max(0, min(score, 100)), {
        "width": width,
        "height": height,
        "sharpness": sharpness,
        "brightness": brightness,
    }
