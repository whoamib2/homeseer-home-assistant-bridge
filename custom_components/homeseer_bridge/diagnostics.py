from __future__ import annotations

from datetime import datetime, timezone

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .repairs_engine import get_cached_repairs_report
from .device_model import summarize_models, model_dict, area_floor_summary
from .bridge_stats import ensure_stats, refresh_derived_stats, health_score, bridge_available, live_device_stats, device_explorer_stats

REDACT_KEYS = {"password", "token", "api_key", "secret", "username"}


def _redact_dict(data: dict) -> dict:
    out = {}
    for key, value in data.items():
        if any(s in str(key).lower() for s in REDACT_KEYS):
            out[key] = "**REDACTED**"
        else:
            out[key] = value
    return out


def _count_by(state: dict, key: str) -> dict:
    counts = {}
    for device in state.values():
        value = str(device.get(key) or "Unknown")
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def _iso(ts):
    if not ts:
        return None
    return datetime.fromtimestamp(float(ts), tz=timezone.utc).isoformat()


async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry: ConfigEntry):
    """Return redacted diagnostics for HomeSeer Bridge."""
    data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
    state = data.get("state") or {}
    topic_lookup = data.get("topic_lookup") or {}
    unmatched = data.get("unmatched_topics") or {}
    stats = ensure_stats(data)
    refresh_derived_stats(stats)
    virtual_refs = data.get("virtual_refs") or set()

    status_counts = {}
    unavailable_refs = []

    for ref, device in state.items():
        status = str(device.get("status") or "Unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
        if status.lower() in {"unknown", "unavailable", "no status"}:
            unavailable_refs.append(ref)

    sample_devices = []
    for ref, device in list(state.items())[:75]:
        sample_devices.append({
            "ref": ref,
            "name": device.get("name"),
            "location": device.get("location"),
            "location2": device.get("location2"),
            "status": device.get("status"),
            "value": device.get("value"),
            "device_type": device.get("device_type"),
            "device_type_string": device.get("device_type_string"),
            "interface": device.get("interface"),
            "interface_name": device.get("interface_name"),
            "is_virtual": ref in virtual_refs,
            "smart_model": model_dict(device, ref),
        })

    return {
        "entry": {
            "title": entry.title,
            "data": _redact_dict(dict(entry.data)),
            "options": _redact_dict(dict(entry.options)),
            "version": entry.version,
            "minor_version": entry.minor_version,
        },
        "live_device_stats": live_device_stats(data),
        "smart_device_model": summarize_models(state),
        "auto_area_prep": area_floor_summary(state),
        "device_explorer": device_explorer_stats(data),
        "repairs": get_cached_repairs_report(data),
        "summary": {
            "health_score": health_score(data),
            "bridge_available": bridge_available(data),
            "devices_loaded": len(state),
            "virtual_devices": len(virtual_refs),
            "topic_lookup_keys": len(topic_lookup),
            "unmatched_topics_seen": len(unmatched),
        },
        "health": {
            "last_api_ok": stats.get("last_api_ok"),
            "consecutive_api_failures": stats.get("consecutive_api_failures"),
            "mqtt_updates": stats.get("mqtt_updates"),
            "api_refreshes": stats.get("api_refreshes"),
            "virtual_polls": stats.get("virtual_polls"),
            "last_virtual_poll_changed": stats.get("last_virtual_poll_changed"),
            "reconnect_attempts": stats.get("reconnect_attempts"),
            "reconnect_successes": stats.get("reconnect_successes"),
            "manual_refreshes": stats.get("manual_refreshes"),
            "manual_reloads": stats.get("manual_reloads"),
            "manual_controls": stats.get("manual_controls"),
            "last_refresh_changed": stats.get("last_refresh_changed"),
            "last_refresh_devices": stats.get("last_refresh_devices"),
            "last_new_devices": stats.get("last_new_devices"),
            "total_new_devices_seen": stats.get("total_new_devices_seen"),
            "last_new_entities_created": stats.get("last_new_entities_created"),
            "total_new_entities_created": stats.get("total_new_entities_created"),
            "metadata_updates": stats.get("metadata_updates"),
            "last_area_apply_changed": stats.get("last_area_apply_changed"),
            "last_area_apply_skipped": stats.get("last_area_apply_skipped"),
            "last_area_apply_dry_run": stats.get("last_area_apply_dry_run"),
            "last_area_apply": stats.get("last_area_apply"),
            "api_latency_ms": stats.get("api_latency_ms"),
            "virtual_poll_latency_ms": stats.get("virtual_poll_latency_ms"),
            "last_mqtt_age_seconds": stats.get("last_mqtt_age_seconds"),
            "last_mqtt_timestamp": _iso(stats.get("last_mqtt_timestamp")),
            "last_api_refresh_timestamp": _iso(stats.get("last_api_refresh_timestamp")),
            "last_virtual_poll_timestamp": _iso(stats.get("last_virtual_poll_timestamp")),
            "integration_started_timestamp": _iso(stats.get("integration_started_timestamp")),
            "recent_activity_count": stats.get("recent_activity_count"),
            "last_activity": stats.get("last_activity"),
            "recent_activity": stats.get("recent_activity") or [],
            "recent_activity_filtered_count": stats.get("recent_activity_filtered_count"),
            "activity_excluded_terms": data.get("activity_excluded_terms") or [],
        },
        "breakdowns": {
            "interfaces": _count_by(state, "interface"),
            "interface_names": _count_by(state, "interface_name"),
            "locations": _count_by(state, "location"),
            "location2": _count_by(state, "location2"),
            "device_types": _count_by(state, "device_type"),
            "device_type_strings": _count_by(state, "device_type_string"),
            "statuses": dict(sorted(status_counts.items())),
        },
        "samples": {
            "unavailable_or_unknown_refs": unavailable_refs[:100],
            "virtual_refs": sorted(list(virtual_refs))[:200],
            "recent_unmatched_topics": dict(list(unmatched.items())[-100:]),
            "devices": sample_devices,
        },
        "raw_stats": stats,
    }
