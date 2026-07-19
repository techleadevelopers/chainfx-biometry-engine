from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter
from typing import Any


@dataclass
class StepTimer:
    timings_ms: dict[str, int] = field(default_factory=dict)

    def measure(self, name: str):
        return _TimerContext(self, name)


class _TimerContext:
    def __init__(self, timer: StepTimer, name: str):
        self.timer = timer
        self.name = name
        self.started = 0.0

    def __enter__(self):
        self.started = perf_counter()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.timer.timings_ms[self.name] = int((perf_counter() - self.started) * 1000)
        return False


def event(name: str, status: str = "ok", **metadata: Any) -> dict[str, Any]:
    return {"event": name, "status": status, "metadata": metadata}
