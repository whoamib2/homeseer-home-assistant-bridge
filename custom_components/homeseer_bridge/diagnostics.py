from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN


async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry: ConfigEntry):
    """Return diagnostics for the HomeSeer Bridge config entry.

    Keep this module intentionally lightweight and defensive so diagnostics
    cannot break integration setup.
    """
    data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
    state = data.get("state") or {}
    topic_lookup = data.get("topic_lookup") or {}
    unmatched = data.get("unmatched_topics") or {}
    stats = data.get("stats") or {}

    interfaces = {}
    device_types = {}

    for device in state.values():
        interface = str(device.get("interface") or "Unknown")
        device_type = str(device.get("device_type") or "Unknown")
        interfaces[interface] = interfaces.get(interface, 0) + 1
        device_types[device_type] = device_types.get(device_type, 0) + 1

    sample_devices = []
    for device in list(state.values())[:50]:
        sample_devices.append(
            {
                "ref": device.get("ref"),
                "name": device.get("name"),
                "location": device.get("location"),
                "location2": device.get("location2"),
                "status": device.get("status"),
                "value": device.get("value"),
                "device_type": device.get("device_type"),
                "interface": device.get("interface"),
            }
        )

    return {
        "entry": {
            "title": entry.title,
            "data_keys": sorted(list(entry.data.keys())),
            "options_keys": sorted(list(entry.options.keys())),
        },
        "counts": {
            "devices_loaded": len(state),
            "topic_lookup_keys": len(topic_lookup),
            "unmatched_topics_seen": len(unmatched),
        },
        "stats": stats,
        "interfaces": dict(sorted(interfaces.items())),
        "device_types": dict(sorted(device_types.items())),
        "recent_unmatched_topics": dict(list(unmatched.items())[-50:]),
        "sample_devices": sample_devices,
    }
