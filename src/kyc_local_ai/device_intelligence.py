from __future__ import annotations

from typing import Any


def evaluate_device(payload: dict[str, Any]) -> dict[str, Any]:
    fingerprint = str(payload.get("DeviceFingerprint", "") or "")
    ip_address = str(payload.get("IPAddress", "") or "")
    signals = {
        "device_id_present": bool(fingerprint),
        "ip_present": bool(ip_address),
        "emulator_detected": bool(payload.get("EmulatorDetected", False)),
        "root_detected": bool(payload.get("RootDetected", False)),
        "vpn_detected": bool(payload.get("VPNDetected", False)),
        "frida_detected": bool(payload.get("FridaDetected", False)),
        "magisk_detected": bool(payload.get("MagiskDetected", False)),
        "timezone": payload.get("Timezone", ""),
        "gps_present": bool(payload.get("GPS")),
        "locale": payload.get("Locale", ""),
        "play_integrity": payload.get("PlayIntegrity", ""),
        "hardware": payload.get("Hardware", ""),
    }
    penalties = 0
    if not signals["device_id_present"]:
        penalties += 18
    if not signals["ip_present"]:
        penalties += 10
    for key in ("emulator_detected", "root_detected", "vpn_detected", "frida_detected", "magisk_detected"):
        if signals[key]:
            penalties += 22
    score = max(0, min(100 - penalties, 100))
    risk = "LOW" if score >= 85 else "MEDIUM" if score >= 65 else "HIGH"
    return {"score": score, "risk": risk, "signals": signals}
