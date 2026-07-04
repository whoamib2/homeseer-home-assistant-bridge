from __future__ import annotations

from time import monotonic


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
    return stats


def mark_mqtt_update(stats: dict) -> None:
    stats["mqtt_updates"] = stats.get("mqtt_updates", 0) + 1
    stats["last_mqtt_monotonic"] = monotonic()
    stats["last_mqtt_age_seconds"] = 0


def record_latency_ms(stats: dict, key: str, start: float) -> None:
    stats[key] = round((monotonic() - start) * 1000, 2)


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
