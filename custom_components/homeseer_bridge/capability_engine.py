from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class StatusMatch:
    value: float | None
    text: str
    semantic: str
    source: str


def _float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _pair_value(pair: dict, *keys):
    for key in keys:
        if key in pair:
            value = _float(pair.get(key))
            if value is not None:
                return value
    return None


def _pair_text(pair: dict) -> str:
    for key in ("Status", "status", "Label", "label", "Text", "text"):
        value = pair.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def _pair_use(pair: dict) -> str:
    return " ".join(
        str(pair.get(key) or "")
        for key in ("ControlUse", "control_use", "StatusUse", "status_use", "Use", "use")
    ).strip().lower()


def status_pairs(device: dict) -> list[dict]:
    pairs = device.get("statuses") or []
    return [pair for pair in pairs if isinstance(pair, dict)]


def control_pairs(device: dict) -> list[dict]:
    pairs = device.get("controls") or []
    return [pair for pair in pairs if isinstance(pair, dict)]


def semantic_from_text(text: str) -> str:
    value = str(text or "").strip().lower()

    # Order matters: "no motion" must be evaluated before "motion".
    inactive = (
        "closed", "is closed", "close",
        "unlocked", "unlock",
        "off", "dry", "clear", "no motion", "normal",
        "idle", "inactive", "not detected", "safe",
    )
    active = (
        "open", "is open", "opened", "tilt",
        "locked", "locking",
        "on", "wet", "water detected", "motion", "detected",
        "alarm", "smoke", "tamper", "active",
    )

    if "jammed" in value:
        return "jammed"
    if "unlocking" in value:
        return "unlocking"
    if "locking" in value:
        return "locking"
    if any(term in value for term in inactive):
        return "inactive"
    if any(term in value for term in active):
        return "active"
    if "unknown" in value:
        return "unknown"
    return "unknown"


def resolve_status_text(device: dict, numeric_value=None) -> StatusMatch:
    """Resolve a raw HomeSeer value using CAPI Status/Graphics metadata."""
    value = _float(numeric_value)
    if value is None:
        value = _float(device.get("numeric_value", device.get("value")))

    # Exact/range lookup from HomeSeer status metadata.
    for pair in status_pairs(device):
        start = _pair_value(pair, "Start", "start", "Value", "value")
        end = _pair_value(pair, "End", "end")
        text = _pair_text(pair)
        if value is None or start is None or not text:
            continue
        if end is None:
            end = start
        if start <= value <= end:
            return StatusMatch(value, text, semantic_from_text(text), "status_metadata")

    # Current HomeSeer status is the next best source.
    current = str(device.get("status") or "").strip()
    if current:
        return StatusMatch(value, current, semantic_from_text(current), "current_status")

    return StatusMatch(value, str(value) if value is not None else "", "unknown", "raw_value")


def has_control_use(device: dict, *uses: str) -> bool:
    wanted = {item.lower() for item in uses}
    for pair in control_pairs(device):
        use = _pair_use(pair)
        if any(item in use for item in wanted):
            return True
    return False


def control_value_for_use(device: dict, *uses: str):
    wanted = {item.lower() for item in uses}
    for pair in control_pairs(device):
        use = _pair_use(pair)
        if any(item in use for item in wanted):
            value = _pair_value(pair, "Value", "value", "Start", "start", "TargetValue", "target_value")
            if value is not None:
                return int(value) if value.is_integer() else value
    return None


def metadata_text(device: dict) -> str:
    status_text = " ".join(_pair_text(pair) for pair in status_pairs(device))
    control_text = " ".join(
        f"{_pair_text(pair)} {_pair_use(pair)}"
        for pair in control_pairs(device)
    )
    base = " ".join(
        str(device.get(key) or "")
        for key in (
            "name", "location", "location2", "status", "device_type",
            "interface", "relationship", "labels_blob", "raw_text",
        )
    )
    return f"{base} {status_text} {control_text}".lower()


def capability_platform(device: dict) -> str:
    """Determine the most likely HA platform from HomeSeer metadata."""
    text = metadata_text(device)

    if has_control_use(device, "doorlock", "doorunlock") or (
        "locked" in text and "unlocked" in text and "lock" in text
    ):
        return "lock"

    if "garage door" in text or "barrier" in text:
        return "cover"

    binary_terms = (
        "door/window", "door window", "door-window", "window/door",
        "contact", "door sensor", "window sensor", "opening sensor",
        "motion", "water leak", "water sensor", "leak", "smoke",
        "carbon monoxide", "co sensor", "tamper",
    )
    if any(term in text for term in binary_terms):
        return "binary_sensor"

    if " fan" in text:
        return "fan"
    if any(term in text for term in ("dimmer", "multilevel", "light", "lamp", "bulb")):
        return "light"
    if any(term in text for term in ("switch", "outlet", "plug", "relay", "module", "virtual")):
        return "switch"
    return "sensor"


def binary_is_on(device: dict) -> bool | None:
    match = resolve_status_text(device)
    if match.semantic == "active":
        return True
    if match.semantic == "inactive":
        return False
    if match.semantic in {"jammed", "locking"}:
        return True
    if match.semantic == "unlocking":
        return False
    return None


def lock_state(device: dict) -> str | None:
    match = resolve_status_text(device)
    text = match.text.lower()

    if "jammed" in text:
        return "jammed"
    if "unlocking" in text:
        return "unlocking"
    if "locking" in text:
        return "locking"
    if "unlocked" in text:
        return "unlocked"
    if "locked" in text:
        return "locked"

    value = match.value
    if value == 0:
        return "unlocked"
    if value == 1:
        return "locked"
    return None


def capability_attributes(device: dict) -> dict[str, Any]:
    match = resolve_status_text(device)
    return {
        "homeseer_capability_platform": capability_platform(device),
        "homeseer_status_source": match.source,
        "homeseer_resolved_status": match.text,
        "homeseer_semantic_state": match.semantic,
        "homeseer_status_pair_count": len(status_pairs(device)),
        "homeseer_control_pair_count": len(control_pairs(device)),
    }
