from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .bridge_stats import ensure_stats, refresh_derived_stats, health_score

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


async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry: ConfigEntry):
    """Return redacted diagnostics for HomeSeer Bridge."""
    data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
    state = data.get("state") or {}
    topic_lookup = data.get("topic_lookup") or {}
    unmatched = data.get("unmatched_topics") or {}
    stats = ensure_stats(data)
    refresh_derived_stats(stats)
    virtual_refs = data.get("virtual_refs") or set()

    platform_counts = {}
    status_counts = {}
    unavailable_refs = []

    for ref, device in state.items():
        device_type = str(device.get("device_type") or device.get("device_type_string") or "Unknown")
        platform_counts[device_type] = platform_counts.get(device_type, 0) + 1

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
        })

    return {
        "entry": {
            "title": entry.title,
            "data": _redact_dict(dict(entry.data)),
            "options": _redact_dict(dict(entry.options)),
            "version": entry.version,
            "minor_version": entry.minor_version,
        },
        "health": {
            "health_score": health_score(data),
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
        },
        "counts": {
            "devices_loaded": len(state),
            "topic_lookup_keys": len(topic_lookup),
            "unmatched_topics_seen": len(unmatched),
            "virtual_devices": len(virtual_refs),
            "unavailable_or_unknown_sample_count": len(unavailable_refs),
        },
        "breakdowns": {
            "interfaces": _count_by(state, "interface"),
            "interface_names": _count_by(state, "interface_name"),
            "locations": _count_by(state, "location"),
            "location2": _count_by(state, "location2"),
            "device_types": dict(sorted(platform_counts.items())),
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
