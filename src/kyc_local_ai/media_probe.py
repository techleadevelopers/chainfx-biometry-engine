from __future__ import annotations

import hashlib
import mimetypes
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import cv2
except Exception:
    cv2 = None


@dataclass
class MediaProbe:
    sha256: str
    size_bytes: int
    mime_type: str
    duration_sec: float | None = None
    fps: float | None = None
    width: int | None = None
    height: int | None = None
    codec: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
            "mime_type": self.mime_type,
            "duration_sec": self.duration_sec,
            "fps": self.fps,
            "width": self.width,
            "height": self.height,
            "codec": self.codec,
        }


def probe(path: Path | None, expected: str) -> tuple[MediaProbe | None, list[str]]:
    if path is None:
        return None, [f"{expected}_missing"]
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    mime_type = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
    flags: list[str] = []
    item = MediaProbe(sha256=digest, size_bytes=len(data), mime_type=mime_type)

    if expected == "video" and cv2 is not None:
        cap = cv2.VideoCapture(str(path))
        fps = float(cap.get(cv2.CAP_PROP_FPS) or 0)
        frames = float(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        item.width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        item.height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        item.fps = fps
        item.duration_sec = frames / fps if fps > 0 else None
        cap.release()
        if item.duration_sec is not None and item.duration_sec > 8:
            flags.append("video_too_long")
        if item.duration_sec is not None and item.duration_sec < 2:
            flags.append("video_too_short")
        if item.width and item.height and min(item.width, item.height) < 360:
            flags.append("video_resolution_low")

    if expected == "image" and not mime_type.startswith("image/"):
        flags.append("invalid_image_mime")
    if expected == "video" and not (mime_type.startswith("video/") or str(path).lower().endswith(".mp4")):
        flags.append("invalid_video_mime")

    return item, flags
