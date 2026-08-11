from __future__ import annotations

import re

from .topic_map import REF_TO_TOPICS
from .device_model import classify_device
from .capability_engine import capability_platform, resolve_status_text, binary_device_class_from_metadata
from .sensor_metadata import classify_sensor

from .const import (
    DOMAIN,
    CONF_EXCLUDED_TERMS,
    CONF_MQTT_PREFIX,
    DEFAULT_EXCLUDED_TERMS,
    DEFAULT_MQTT_PREFIX,
)

def _topic_part(value: str) -> str:
    # mcsMQTT commonly replaces spaces with underscores while preserving parentheses/punctuation.
    return str(value or "").strip().replace(" ", "_")

def normalize_topic(value: str) -> str:
    # Normalize enough to match HomeSeer/mcsMQTT formatting differences.
    value = str(value or "").strip().lower()
    value = value.replace(" ", "_")
    value = re.sub(r"/+", "/", value)
    return value.rstrip("/")

def mqtt_prefix(entry) -> str:
    return entry.options.get(CONF_MQTT_PREFIX, entry.data.get(CONF_MQTT_PREFIX, DEFAULT_MQTT_PREFIX)).rstrip("/")

def mqtt_topic(device: dict, entry) -> str:
    prefix = mqtt_prefix(entry)
    parts = [
        prefix,
        _topic_part(device.get("location2")),
        _topic_part(device.get("location")),
        _topic_part(device.get("name")),
    ]
    return "/".join(p for p in parts if p)

def topic_candidates(device: dict, entry) -> set[str]:
    prefix = mqtt_prefix(entry)
    loc2 = _topic_part(device.get("location2"))
    loc = _topic_part(device.get("location"))
    name = _topic_part(device.get("name"))

    candidates = set()
    if loc2 and loc and name:
        candidates.add(f"{prefix}/{loc2}/{loc}/{name}")
    if loc2 and name:
        candidates.add(f"{prefix}/{loc2}/{name}")
    if loc and name:
        candidates.add(f"{prefix}/{loc}/{name}")
    if name:
        candidates.add(f"{prefix}/{name}")

    return candidates

def build_topic_lookup(devices: dict[int, dict], entry) -> dict[str, int]:
    """Build O(1) MQTT topic -> HomeSeer ref lookup.

    v1.1 uses the exact mcsMQTT database mapping first, then falls back to
    generated topic candidates. This avoids 10-15 second delayed updates caused
    by topic guesses not matching real mcsMQTT topics.
    """
    lookup = {}

    # Exact topic mapping generated from mcsMQTT.db
    for ref, topics in REF_TO_TOPICS.items():
        if ref not in devices:
            continue
        for topic in topics:
            lookup[normalize_topic(topic)] = ref
            last = normalize_topic(topic).split("/")[-1]
            lookup.setdefault(f"__name__/{last}", ref)

    # Fallback generated candidates
    for ref, device in devices.items():
        for candidate in topic_candidates(device, entry):
            lookup.setdefault(normalize_topic(candidate), ref)

        name_key = f"__name__/{normalize_topic(_topic_part(device.get('name')))}"
        lookup.setdefault(name_key, ref)

    return lookup

def topic_to_ref(topic: str, lookup: dict[str, int]) -> int | None:
    normalized = normalize_topic(topic)
    if normalized in lookup:
        return lookup[normalized]

    last = normalized.split("/")[-1] if normalized else ""
    return lookup.get(f"__name__/{last}")

def full_name(device: dict) -> str:
    parts = [device.get("location2"), device.get("location"), device.get("name")]
    return " ".join(str(p).strip() for p in parts if p)


def _clean_registry_value(value):
    if value is None:
        return None
    value = str(value).strip()
    return value or None

def bridge_device_info() -> dict:
    return {
        "identifiers": {(DOMAIN, "bridge")},
        "name": "HomeSeer Bridge",
        "manufacturer": "HomeSeer",
        "model": "HS4 Bridge",
    }

def device_info(device: dict, ref=None) -> dict:
    hs_ref = device.get("ref") or device.get("Ref") or ref

    parts = [
        _clean_registry_value(device.get("interface") or device.get("interface_name")),
        _clean_registry_value(
            device.get("device_type_string")
            or device.get("device_type")
            or device.get("Device_Type_Description")
            or device.get("device_type_description")
        ),
    ]
    parts = [part for part in parts if part and part.lower() != "unknown"]
    model_info = classify_device(device, hs_ref)
    model = model_info.device_type or model_info.category or (" / ".join(parts) if parts else "HS4 Device")

    info = {
        "identifiers": {(DOMAIN, str(hs_ref))},
        "name": full_name(device),
        "manufacturer": "HomeSeer",
        "model": model,
        "via_device": (DOMAIN, "bridge"),
    }

    suggested_area = _clean_registry_value(device.get("location2")) or _clean_registry_value(device.get("location"))
    if suggested_area:
        info["suggested_area"] = suggested_area

    sw_version = _clean_registry_value(device.get("version") or device.get("firmware") or device.get("firmware_version"))
    if sw_version:
        info["sw_version"] = sw_version

    return info


def text_blob(device: dict) -> str:
    return " ".join([
        str(device.get("name", "")),
        str(device.get("location", "")),
        str(device.get("location2", "")),
        str(device.get("status", "")),
        str(device.get("device_type", "")),
        str(device.get("interface", "")),
        str(device.get("labels_blob", "")),
        str(device.get("raw_text", "")),
    ]).lower()

def excluded_terms(entry) -> list[str]:
    raw = entry.options.get(
        CONF_EXCLUDED_TERMS,
        entry.data.get(CONF_EXCLUDED_TERMS, DEFAULT_EXCLUDED_TERMS),
    )
    return [x.strip().lower() for x in str(raw).split(",") if x.strip()]


def is_excluded(device: dict, entry) -> bool:
    """Return True when a feature is excluded by text or exact HomeSeer ref.

    Text exclusions match the feature metadata blob. A token like ``ref:3174``
    is an exact, durable exclusion used when a user manually removes a device
    from Home Assistant.
    """
    ref = device.get("ref") or device.get("Ref")
    ref_text = str(ref) if ref is not None else ""
    text = text_blob(device)

    for term in excluded_terms(entry):
        if term.startswith("ref:"):
            if term[4:].strip() == ref_text:
                return True
            continue
        if term in text:
            return True
    return False


def split_excluded_devices(
    devices: dict[int, dict], entry
) -> tuple[dict[int, dict], dict[int, dict]]:
    """Split HomeSeer data into active and excluded state dictionaries."""
    included: dict[int, dict] = {}
    excluded: dict[int, dict] = {}

    for ref, device in devices.items():
        if is_excluded(device, entry):
            excluded[ref] = device
        else:
            included[ref] = device

    return included, excluded

def parse_payload(payload) -> tuple[float | None, str]:
    status = str(payload).strip()
    try:
        return float(status), status
    except Exception:
        return None, status

def apply_mqtt_state(device: dict, payload):
    numeric, status = parse_payload(payload)
    previous_numeric = device.get("numeric_value")
    previous_status = str(device.get("status") or "")
    device["value"] = payload
    device["numeric_value"] = numeric

    platform = capability_platform(device)

    # Measurement and battery sensors must retain their raw numeric readings.
    # They should never be translated to generic On/Off text.
    if platform == "sensor":
        device["status"] = status
        device["status_source"] = "mqtt_numeric_sensor" if numeric is not None else "mqtt_text_sensor"
        device["semantic_state"] = "measurement" if numeric is not None else "text"
        return

    # Locks use HomeSeer's lock status vocabulary and numeric values.
    if platform == "lock":
        match = resolve_status_text(device, numeric)
        if match.source == "status_metadata":
            device["status"] = match.text or status
        else:
            lock_numeric = numeric
            if lock_numeric in {0, 1, 16, 17, 32, 33}:
                device["status"] = "Unsecured"
                device["last_known_lock_state"] = "unlocked"
            elif lock_numeric == 255:
                device["status"] = "Secured"
                device["last_known_lock_state"] = "locked"
            elif lock_numeric == 254:
                # Preserve the last reliable state instead of oscillating to
                # Unknown when HomeSeer emits a transient 254.
                device["status"] = (
                    "Secured"
                    if device.get("last_known_lock_state") == "locked"
                    else "Unsecured"
                    if device.get("last_known_lock_state") == "unlocked"
                    else "Unknown"
                )
            else:
                device["status"] = status
        device["status_source"] = "mqtt_lock"
        device["semantic_state"] = device.get("last_known_lock_state") or "unknown"
        return

    # Preserve a semantic map learned from HomeSeer's API status/value pair.
    value_status_map = device.setdefault("value_status_map", {})
    if previous_numeric is not None and previous_status:
        try:
            previous_key = str(
                int(float(previous_numeric))
                if float(previous_numeric).is_integer()
                else float(previous_numeric)
            )
            previous_lower = previous_status.strip().lower()
            inactive_terms = ("closed", "off", "clear", "dry", "no motion", "normal", "idle", "unlocked", "unsecured")
            active_terms = ("open", "on", "detected", "motion", "wet", "alarm", "smoke", "locked", "secured", "tamper")
            if any(term in previous_lower for term in inactive_terms):
                value_status_map[previous_key] = "inactive"
            elif any(term in previous_lower for term in active_terms):
                value_status_map[previous_key] = "active"
        except (TypeError, ValueError):
            pass

    if numeric is not None:
        match = resolve_status_text(device, numeric)

        if match.source == "status_metadata":
            device["status"] = match.text or status
            device["status_source"] = match.source
            device["semantic_state"] = match.semantic
            return

        numeric_key = str(int(numeric) if numeric.is_integer() else numeric)
        semantic = value_status_map.get(numeric_key)

        if semantic is None and numeric == 0:
            semantic = "inactive"
        elif semantic is None and numeric in {1, 100, 255}:
            semantic = "active"

        if semantic is not None:
            device["semantic_state"] = semantic
            device["status_source"] = "mqtt_numeric"
            device["status"] = "On" if semantic == "active" else "Off"
        else:
            device["status"] = status
            device["status_source"] = "mqtt_numeric_raw"
            device["semantic_state"] = "unknown"
    else:
        device["status"] = status
        device["status_source"] = "mqtt_text"

def has_on_off_controls(device: dict) -> bool:
    labels = str(device.get("labels_blob", "")).lower()
    values = set()

    for v in device.get("control_values", []):
        try:
            values.add(int(float(v)))
        except Exception:
            pass

    return (
        ("on" in labels and "off" in labels)
        or ({0, 255}.issubset(values))
        or ({0, 100}.issubset(values))
        or ({0, 1}.issubset(values))
    )

def is_lock(device: dict) -> bool:
    return capability_platform(device) == "lock"

def is_cover(device: dict) -> bool:
    return capability_platform(device) == "cover"

def is_binary_sensor(device: dict) -> bool:
    return capability_platform(device) == "binary_sensor"

def is_fan(device: dict) -> bool:
    return capability_platform(device) == "fan"

def is_dimmer(device: dict) -> bool:
    # Historical helper name retained for light.py compatibility.
    return capability_platform(device) == "light"

def is_controllable_switch(device: dict) -> bool:
    if device.get("hide"):
        return False
    return capability_platform(device) == "switch"

def is_plain_sensor(device: dict) -> bool:
    return capability_platform(device) == "sensor"

def binary_device_class(device: dict) -> str | None:
    return binary_device_class_from_metadata(device)

def sensor_device_class(device: dict) -> str | None:
    return classify_sensor(device).device_class

def unit_of_measurement(device: dict) -> str | None:
    return classify_sensor(device).unit

def sensor_state_class(device: dict) -> str | None:
    return classify_sensor(device).state_class

def sensor_category(device: dict) -> str:
    return classify_sensor(device).category

def on_value(device: dict):
    values = set()

    for v in device.get("control_values", []):
        try:
            values.add(int(float(v)))
        except Exception:
            pass

    if 255 in values:
        return 255
    if 100 in values:
        return 100
    if 1 in values:
        return 1
    return 255

def off_value(device: dict):
    return 0
