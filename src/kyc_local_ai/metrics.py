from __future__ import annotations

import time
from collections import defaultdict
from threading import Lock
from typing import Any


class Metrics:
    def __init__(self) -> None:
        self._lock = Lock()
        self.requests_total = 0
        self.decision_total: dict[str, int] = defaultdict(int)
        self.latency_ms: list[int] = []
        self.step_latency_ms: dict[str, list[int]] = defaultdict(list)

    def record(self, result: dict[str, Any]) -> None:
        with self._lock:
            self.requests_total += 1
            self.decision_total[str(result.get("decision", "unknown"))] += 1
            self.latency_ms.append(int(result.get("latency_ms", 0)))
            timings = result.get("details", {}).get("timings_ms", {})
            if isinstance(timings, dict):
                for name, value in timings.items():
                    try:
                        self.step_latency_ms[name].append(int(value))
                    except (TypeError, ValueError):
                        continue

    def prometheus(self) -> str:
        with self._lock:
            lines = [
                "# HELP kyc_requests_total Total KYC analysis requests.",
                "# TYPE kyc_requests_total counter",
                f"kyc_requests_total {self.requests_total}",
                "# HELP kyc_decisions_total Total KYC decisions by status.",
                "# TYPE kyc_decisions_total counter",
            ]
            for decision, count in sorted(self.decision_total.items()):
                lines.append(f'kyc_decisions_total{{decision="{decision}"}} {count}')

            lines.extend([
                "# HELP kyc_latency_seconds Last observed total latency.",
                "# TYPE kyc_latency_seconds gauge",
                f"kyc_latency_seconds {self._last_seconds(self.latency_ms)}",
                "# HELP kyc_step_latency_seconds Last observed step latency.",
                "# TYPE kyc_step_latency_seconds gauge",
            ])
            for name, values in sorted(self.step_latency_ms.items()):
                metric = name[:-3] if name.endswith("_ms") else name
                lines.append(f'kyc_step_latency_seconds{{step="{metric}"}} {self._last_seconds(values)}')
            lines.append(f"kyc_metrics_generated_at {int(time.time())}")
            return "\n".join(lines) + "\n"

    @staticmethod
    def _last_seconds(values: list[int]) -> str:
        if not values:
            return "0"
        return f"{values[-1] / 1000:.6f}"


metrics = Metrics()
