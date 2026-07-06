from __future__ import annotations

import re

from .topic_map import REF_TO_TOPICS

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
    model = " / ".join(parts) if parts else "HS4 Device"

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
    raw = entry.options.get(CONF_EXCLUDED_TERMS, entry.data.get(CONF_EXCLUDED_TERMS, DEFAULT_EXCLUDED_TERMS))
    return [x.strip().lower() for x in str(raw).split(",") if x.strip()]

def is_excluded(device: dict, entry) -> bool:
    text = text_blob(device)
    return any(term in text for term in excluded_terms(entry))

def parse_payload(payload) -> tuple[float | None, str]:
    status = str(payload).strip()
    try:
        return float(status), status
    except Exception:
        return None, status

def apply_mqtt_state(device: dict, payload):
    numeric, status = parse_payload(payload)
    device["value"] = payload
    device["numeric_value"] = numeric

    if numeric is not None:
        device["status"] = "On" if numeric > 0 else "Off"
    else:
        device["status"] = status

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
    text = text_blob(device)
    labels = str(device.get("labels_blob", "")).lower()
    return "door lock" in text or " lock" in text or ("locked" in labels and "unlocked" in labels)

def is_cover(device: dict) -> bool:
    text = text_blob(device)
    labels = str(device.get("labels_blob", "")).lower()
    return "garage door" in text or "barrier" in text or ("open" in labels and "close" in labels and "garage" in text)

def is_binary_sensor(device: dict) -> bool:
    text = text_blob(device)
    return any(k in text for k in [
        "motion",
        "contact",
        "leak",
        "smoke",
        "co sensor",
        "water sensor",
        "door sensor",
        "window sensor",
        "tamper",
    ])

def is_fan(device: dict) -> bool:
    text = text_blob(device)
    return " fan" in text and has_on_off_controls(device) and not is_binary_sensor(device)

def is_dimmer(device: dict) -> bool:
    text = text_blob(device)
    labels = str(device.get("labels_blob", "")).lower()
    return (
        ("dimmer" in text or "multilevel" in text or "level" in labels or "dim" in labels)
        and not is_lock(device)
        and not is_cover(device)
    )

def is_controllable_switch(device: dict) -> bool:
    if device.get("hide"):
        return False

    if is_lock(device) or is_cover(device) or is_binary_sensor(device) or is_fan(device) or is_dimmer(device):
        return False

    text = text_blob(device)

    if has_on_off_controls(device):
        if any(k in text for k in [
            "switch",
            "outlet",
            "plug",
            "module",
            "relay",
            "light",
            "lamp",
            "valve",
            "water valve",
            "pump",
            "siren",
            "appliance",
            "scene",
            "virtual",
        ]):
            return True

    if any(k in text for k in ["valve", "water valve", "switch binary", "switch", "outlet", "plug", "relay", "module"]):
        return True

    return False

def is_plain_sensor(device: dict) -> bool:
    return not (
        is_controllable_switch(device)
        or is_dimmer(device)
        or is_lock(device)
        or is_cover(device)
        or is_binary_sensor(device)
        or is_fan(device)
    )

def binary_device_class(device: dict) -> str | None:
    text = text_blob(device)
    if "motion" in text:
        return "motion"
    if "leak" in text or "water sensor" in text or "water" in text:
        return "moisture"
    if "smoke" in text:
        return "smoke"
    if "tamper" in text:
        return "tamper"
    if "door" in text or "window" in text or "contact" in text:
        return "opening"
    return None

def sensor_device_class(device: dict) -> str | None:
    text = text_blob(device)
    if "temperature" in text or " temp" in text:
        return "temperature"
    if "humidity" in text:
        return "humidity"
    if "battery" in text:
        return "battery"
    if "power" in text or "watts" in text:
        return "power"
    if "energy" in text or "kwh" in text:
        return "energy"
    if "illuminance" in text or "luminance" in text or "lux" in text:
        return "illuminance"
    return None

def unit_of_measurement(device: dict) -> str | None:
    text = text_blob(device)
    if "temperature" in text or " temp" in text:
        return "°F"
    if "humidity" in text or "battery" in text:
        return "%"
    if "watts" in text or "power" in text:
        return "W"
    if "kwh" in text or "energy" in text:
        return "kWh"
    if "lux" in text or "illuminance" in text or "luminance" in text:
        return "lx"
    return None

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
