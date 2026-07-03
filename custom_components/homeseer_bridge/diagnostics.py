from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_HS_URL, CONF_MQTT_PREFIX, CONF_EXCLUDED_TERMS, CONF_ENABLE_DEBUG_LOGGING
from .helpers import is_excluded, text_blob

async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry: ConfigEntry):
    data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
    state = data.get("state", {})
    topic_lookup = data.get("topic_lookup", {})
    unmatched = data.get("unmatched_topics", {})

    platform_counts = {}
    excluded_count = 0
    interfaces = {}

    for device in state.values():
        interface = device.get("interface") or "Unknown"
        interfaces[interface] = interfaces.get(interface, 0) + 1
        if is_excluded(device, entry):
            excluded_count += 1
        model = device.get("device_type") or "Unknown"
        platform_counts[model] = platform_counts.get(model, 0) + 1

    return {
        "entry": {
            "title": entry.title,
            "data": {
                CONF_HS_URL: entry.data.get(CONF_HS_URL),
                CONF_MQTT_PREFIX: entry.data.get(CONF_MQTT_PREFIX),
                CONF_EXCLUDED_TERMS: entry.data.get(CONF_EXCLUDED_TERMS),
                CONF_ENABLE_DEBUG_LOGGING: entry.data.get(CONF_ENABLE_DEBUG_LOGGING),
            },
            "options": dict(entry.options),
        },
        "counts": {
            "devices_loaded": len(state),
            "topic_lookup_keys": len(topic_lookup),
            "excluded_devices": excluded_count,
            "unmatched_topics_seen": len(unmatched),
        },
        "interfaces": dict(sorted(interfaces.items())),
        "device_type_counts": dict(sorted(platform_counts.items())),
        "recent_unmatched_topics": dict(list(unmatched.items())[-50:]),
        "sample_devices": [
            {
                "ref": d.get("ref"),
                "name": d.get("name"),
                "location": d.get("location"),
                "location2": d.get("location2"),
                "status": d.get("status"),
                "value": d.get("value"),
                "device_type": d.get("device_type"),
                "interface": d.get("interface"),
                "excluded": is_excluded(d, entry),
            }
            for d in list(state.values())[:50]
        ],
    }
