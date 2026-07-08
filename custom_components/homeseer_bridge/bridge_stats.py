from __future__ import annotations

from time import monotonic, time

from .device_model import summarize_models, category_count, area_floor_summary

MAX_RECENT_ACTIVITY = 50


def ensure_stats(data: dict) -> dict:
    stats = data.setdefault("stats", {})
    stats.setdefault("mqtt_updates", 0)
    stats.setdefault("api_refreshes", 0)
    stats.setdefault("virtual_polls", 0)
    stats.setdefault("reconnect_attempts", 0)
    stats.setdefault("reconnect_successes", 0)
    stats.setdefault("manual_refreshes", 0)
    stats.setdefault("manual_reloads", 0)
    stats.setdefault("manual_controls", 0)
    stats.setdefault("last_api_ok", True)
    stats.setdefault("consecutive_api_failures", 0)
    stats.setdefault("last_refresh_changed", 0)
    stats.setdefault("last_refresh_devices", 0)
    stats.setdefault("last_new_devices", 0)
    stats.setdefault("total_new_devices_seen", 0)
    stats.setdefault("virtual_devices", 0)
    stats.setdefault("last_virtual_poll_changed", 0)
    stats.setdefault("api_latency_ms", None)
    stats.setdefault("virtual_poll_latency_ms", None)
    stats.setdefault("last_mqtt_age_seconds", None)
    stats.setdefault("last_mqtt_monotonic", None)
    stats.setdefault("last_mqtt_timestamp", None)
    stats.setdefault("last_api_refresh_timestamp", None)
    stats.setdefault("last_virtual_poll_timestamp", None)
    stats.setdefault("integration_started_timestamp", stats.get("integration_started_timestamp") or time())
    stats.setdefault("recent_activity", [])
    stats.setdefault("recent_activity_count", 0)
    stats.setdefault("recent_activity_filtered_count", 0)
    stats.setdefault("last_activity", None)
    return stats


def mark_mqtt_update(stats: dict) -> None:
    stats["mqtt_updates"] = stats.get("mqtt_updates", 0) + 1
    stats["last_mqtt_monotonic"] = monotonic()
    stats["last_mqtt_timestamp"] = time()
    stats["last_mqtt_age_seconds"] = 0


def record_latency_ms(stats: dict, key: str, start: float) -> None:
    stats[key] = round((monotonic() - start) * 1000, 2)


def mark_api_refresh(stats: dict) -> None:
    stats["last_api_refresh_timestamp"] = time()


def mark_virtual_poll(stats: dict) -> None:
    stats["last_virtual_poll_timestamp"] = time()


def refresh_derived_stats(stats: dict) -> None:
    last_mqtt = stats.get("last_mqtt_monotonic")
    if last_mqtt is not None:
        stats["last_mqtt_age_seconds"] = round(monotonic() - last_mqtt, 1)


def health_score(data: dict) -> int:
    stats = ensure_stats(data)
    unmatched = data.get("unmatched_topics") or {}

    score = 100

    if not stats.get("last_api_ok", True):
        score -= 30

    failures = int(stats.get("consecutive_api_failures") or 0)
    score -= min(30, failures * 5)

    latency = stats.get("api_latency_ms")
    if isinstance(latency, (int, float)):
        if latency > 5000:
            score -= 20
        elif latency > 2000:
            score -= 10
        elif latency > 1000:
            score -= 5

    unmatched_count = len(unmatched)
    if unmatched_count > 100:
        score -= 15
    elif unmatched_count > 25:
        score -= 10
    elif unmatched_count > 0:
        score -= 3

    return max(0, min(100, score))


def bridge_available(data: dict) -> bool:
    stats = ensure_stats(data)
    return bool(stats.get("last_api_ok", True)) and health_score(data) >= 50
def _device_text(device: dict) -> str:
    return " ".join(
        str(device.get(key) or "")
        for key in (
            "name",
            "location",
            "location2",
            "status",
            "device_type",
            "device_type_string",
            "Device_Type_Description",
            "device_type_description",
            "interface",
            "interface_name",
            "labels_blob",
            "raw_text",
        )
    ).lower()


def _numeric_value(device: dict):
    value = device.get("numeric_value", device.get("value"))
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _status(device: dict) -> str:
    return str(device.get("status") or "").strip().lower()


def _is_on_like(device: dict) -> bool:
    value = _numeric_value(device)
    if value is not None:
        return value > 0
    return _status(device) in {"on", "open", "unlocked", "active", "motion", "detected", "wet", "true", "yes"}


def _is_off_like(device: dict) -> bool:
    value = _numeric_value(device)
    if value is not None:
        return value == 0
    return _status(device) in {"off", "closed", "locked", "idle", "clear", "dry", "false", "no"}


def live_device_stats(data: dict) -> dict:
    """Return dashboard-friendly live statistics from the current HomeSeer state."""
    state = data.get("state") or {}
    stats = ensure_stats(data)
    refresh_derived_stats(stats)

    result = {
        "devices_on": 0,
        "devices_off": 0,
        "devices_unknown": 0,
        "lights_on": 0,
        "lights_off": 0,
        "switches_on": 0,
        "switches_off": 0,
        "binary_sensors_on": 0,
        "binary_sensors_off": 0,
        "covers_open": 0,
        "covers_closed": 0,
        "locks_unlocked": 0,
        "locks_locked": 0,
        "fans_on": 0,
        "fans_off": 0,
        "climate_active": 0,
        "low_battery_devices": 0,
        "mqtt_updates_per_min": 0,
        "api_refreshes_per_hour": 0,
        "virtual_polls_per_min": 0,
        "uptime_seconds": 0,
    }

    for device in state.values():
        text = _device_text(device)
        status = _status(device)
        value = _numeric_value(device)
        is_on = _is_on_like(device)
        is_off = _is_off_like(device)

        if is_on:
            result["devices_on"] += 1
        elif is_off:
            result["devices_off"] += 1
        else:
            result["devices_unknown"] += 1

        is_light = "light" in text or "dimmer" in text or "lamp" in text
        is_switch = "switch" in text or "virtual" in text
        is_binary = any(word in text for word in ("motion", "contact", "leak", "water sensor", "door sensor", "window sensor", "tamper", "smoke", "co sensor"))
        is_cover = "garage door" in text or "barrier" in text or "cover" in text
        is_lock = "lock" in text
        is_fan = "fan" in text
        is_climate = any(word in text for word in ("thermostat", "climate", "heat", "cooling", "heating"))

        if is_light:
            result["lights_on" if is_on else "lights_off"] += 1
        if is_switch:
            result["switches_on" if is_on else "switches_off"] += 1
        if is_binary:
            result["binary_sensors_on" if is_on else "binary_sensors_off"] += 1
        if is_cover:
            result["covers_open" if ("open" in status or is_on) else "covers_closed"] += 1
        if is_lock:
            result["locks_unlocked" if ("unlock" in status or (value == 0 if value is not None else False)) else "locks_locked"] += 1
        if is_fan:
            result["fans_on" if is_on else "fans_off"] += 1
        if is_climate and any(word in status for word in ("heat", "cool", "heating", "cooling", "active")):
            result["climate_active"] += 1

        if "battery" in text and value is not None and value <= 20:
            result["low_battery_devices"] += 1

    started = stats.get("integration_started_timestamp")
    now = time()
    if started:
        uptime = max(0, now - float(started))
        result["uptime_seconds"] = round(uptime)
        if uptime > 0:
            result["mqtt_updates_per_min"] = round((stats.get("mqtt_updates", 0) / uptime) * 60, 2)
            result["api_refreshes_per_hour"] = round((stats.get("api_refreshes", 0) / uptime) * 3600, 2)
            result["virtual_polls_per_min"] = round((stats.get("virtual_polls", 0) / uptime) * 60, 2)

    return result

def _activity_text(device: dict | None) -> str:
    if not device:
        return ""
    return " ".join(
        str(device.get(key) or "")
        for key in (
            "name",
            "location",
            "location2",
            "status",
            "value",
            "numeric_value",
            "device_type",
            "device_type_string",
            "Device_Type_Description",
            "device_type_description",
            "interface",
            "interface_name",
            "labels_blob",
            "raw_text",
        )
    ).lower()


def _activity_is_excluded(data: dict, old_device: dict | None, new_device: dict | None) -> bool:
    terms = data.get("activity_excluded_terms") or []
    if not terms:
        return False
    text = f"{_activity_text(old_device)} {_activity_text(new_device)}"
    return any(term in text for term in terms)

def _activity_value(device: dict | None):
    if not device:
        return None
    if device.get("status") not in (None, ""):
        return device.get("status")
    if device.get("numeric_value") is not None:
        return device.get("numeric_value")
    return device.get("value")


def _activity_name(device: dict | None, ref) -> str:
    if not device:
        return f"HomeSeer Ref {ref}"
    parts = [device.get("location2"), device.get("location"), device.get("name")]
    name = " ".join(str(p).strip() for p in parts if p)
    return name or f"HomeSeer Ref {ref}"


def record_recent_activity(data: dict, ref, old_device: dict | None, new_device: dict | None, source: str) -> None:
    """Record a compact recent activity event for dashboards and diagnostics."""
    stats = ensure_stats(data)
    if _activity_is_excluded(data, old_device, new_device):
        stats["recent_activity_filtered_count"] = stats.get("recent_activity_filtered_count", 0) + 1
        return
    old_value = _activity_value(old_device)
    new_value = _activity_value(new_device)

    # Avoid noise where the caller detected only metadata changes.
    if old_value == new_value and old_device is not None:
        old_name = _activity_name(old_device, ref)
        new_name = _activity_name(new_device, ref)
        if old_name == new_name:
            return

    event = {
        "timestamp": time(),
        "ref": ref,
        "name": _activity_name(new_device or old_device, ref),
        "source": source,
        "old": old_value,
        "new": new_value,
    }

    activity = list(stats.get("recent_activity") or [])
    activity.insert(0, event)
    del activity[MAX_RECENT_ACTIVITY:]
    stats["recent_activity"] = activity
    stats["recent_activity_count"] = stats.get("recent_activity_count", 0) + 1

    old_text = "" if old_value is None else str(old_value)
    new_text = "" if new_value is None else str(new_value)
    stats["last_activity"] = f"{event['name']}: {old_text} → {new_text}".strip()
def smart_model_stats(data: dict) -> dict:
    return summarize_models(data.get("state") or {})
def area_floor_stats(data: dict) -> dict:
    return area_floor_summary(data.get("state") or {})
