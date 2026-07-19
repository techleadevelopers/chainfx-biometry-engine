from __future__ import annotations

import re
from typing import Any


URL_FIELDS = ("DocumentURL", "DocumentBackURL", "SelfieURL", "FacialVideoURL")


def validate_payload(payload: Any) -> tuple[bool, list[str]]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return False, ["payload_must_be_object"]

    for field in ("RequestID", "UserID"):
        value = payload.get(field)
        if value is not None and not isinstance(value, str):
            errors.append(f"{field}_must_be_string")

    level = payload.get("Level", 1)
    if not isinstance(level, int) or level < 1 or level > 3:
        errors.append("Level_must_be_1_2_or_3")

    for field in URL_FIELDS:
        value = payload.get(field, "")
        if value and not isinstance(value, str):
            errors.append(f"{field}_must_be_string")
        if isinstance(value, str) and value and not re.match(r"^https?://", value):
            errors.append(f"{field}_must_be_http_url")

    return len(errors) == 0, errors
