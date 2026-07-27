from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .sensor_metadata import is_strong_sensor_feature


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
    """Determine the HA platform using the feature's own identity first."""
    text = metadata_text(device)
    own_text = " ".join(
        str(device.get(key) or "").lower()
        for key in ("name", "device_type", "interface", "relationship", "status")
    )

    # Battery and measurement children must not inherit their parent's type.
    if is_strong_sensor_feature(device):
        return "sensor"

    if has_control_use(device, "doorlock", "doorunlock") or (
        "locked" in own_text and "unlocked" in own_text and "lock" in own_text
    ):
        return "lock"

    if "garage door" in own_text or "barrier" in own_text:
        return "cover"

    binary_terms = (
        "door/window", "door window", "door-window", "window/door",
        "contact", "door sensor", "window sensor", "opening sensor",
        "motion", "water leak", "water sensor", "leak", "smoke",
        "carbon monoxide", "co sensor", "tamper",
    )
    if any(term in own_text for term in binary_terms):
        return "binary_sensor"

    if " fan" in own_text:
        return "fan"
    if any(term in own_text for term in ("dimmer", "multilevel", "light", "lamp", "bulb")):
        return "light"
    if any(term in own_text for term in ("switch", "outlet", "plug", "relay", "module", "virtual")):
        return "switch"

    if any(term in text for term in binary_terms):
        return "binary_sensor"
    return "sensor"


def binary_is_on(device: dict) -> bool | None:
    """Return a binary state without allowing stale HomeSeer text to win.

    mcsMQTT commonly publishes raw numeric values while HomeSeer's JSON API
    still contains the previous status string. For example, a door sensor may
    publish 0/255 while the cached text remains "On-Open-Motion". When no CAPI
    status-pair match is available, the MQTT numeric value is authoritative.
    """
    match = resolve_status_text(device)

    if match.source == "status_metadata":
        if match.semantic == "active":
            return True
        if match.semantic == "inactive":
            return False
        if match.semantic in {"jammed", "locking"}:
            return True
        if match.semantic == "unlocking":
            return False

    numeric = _float(device.get("numeric_value", device.get("value")))
    if numeric is not None:
        known = device.get("value_status_map") or {}
        mapped = known.get(str(int(numeric) if numeric.is_integer() else numeric))
        if mapped == "active":
            return True
        if mapped == "inactive":
            return False

        # Standard HomeSeer/mcsMQTT binary values.
        if numeric == 0:
            return False
        if numeric in {1, 100, 255}:
            return True

    # Use current text only when no useful numeric value exists.
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
    """Translate HomeSeer lock terminology and values to HA lock states."""
    match = resolve_status_text(device)
    text = match.text.lower().strip()

    # Check negative/unsecured forms before secured/locked substrings.
    if "jammed" in text:
        return "jammed"
    if "unlocking" in text:
        return "unlocking"
    if "locking" in text:
        return "locking"
    if "unsecured" in text or "unlocked" in text or text == "unlock":
        return "unlocked"
    if "secured" in text or "locked" in text or text == "lock":
        return "locked"

    value = match.value
    if value is None:
        value = _float(device.get("numeric_value", device.get("value")))

    # HomeSeer Z-Wave door-lock status values:
    # 0/1/16/17/32/33 are unsecured variants, 255 is secured,
    # and 254 means HomeSeer temporarily cannot determine the state.
    if value in {0, 1, 16, 17, 32, 33}:
        return "unlocked"
    if value == 255:
        return "locked"
    if value == 254:
        previous = device.get("last_known_lock_state")
        if previous in {"locked", "unlocked", "locking", "unlocking", "jammed"}:
            return previous
        return None
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


def binary_device_class_from_metadata(device: dict) -> str | None:
    """Resolve a Home Assistant binary-sensor device class from HomeSeer metadata."""
    text = metadata_text(device)

    door_terms = (
        "door/window",
        "door window",
        "door-window",
        "window/door",
        "door sensor",
        "door contact",
        "front door",
        "back door",
        "entry door",
    )
    window_terms = (
        "window sensor",
        "window contact",
        "window open",
        "window closed",
    )

    if any(term in text for term in door_terms):
        return "door"
    if any(term in text for term in window_terms):
        return "window"
    if any(term in text for term in ("contact sensor", "opening sensor", "contact", "opening")):
        return "opening"

    if any(term in text for term in ("water leak", "leak sensor", "water sensor", "moisture", "flood")):
        return "moisture"
    if "smoke" in text:
        return "smoke"
    if any(term in text for term in ("carbon monoxide", "co sensor", "co alarm")):
        return "carbon_monoxide"
    if any(term in text for term in ("gas leak", "combustible gas", "natural gas")):
        return "gas"
    if "tamper" in text:
        return "tamper"
    if any(term in text for term in ("vibration", "shock sensor", "glass break")):
        return "vibration"
    if "occupancy" in text:
        return "occupancy"
    if any(term in text for term in ("presence sensor", "presence detected")):
        return "presence"
    if any(term in text for term in ("motion sensor", "motion detector", "pir sensor", "motion")):
        return "motion"

    return None
