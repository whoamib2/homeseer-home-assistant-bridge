from __future__ import annotations

from homeassistant.components.sensor import SensorEntity

from .const import DOMAIN
from .entity_base import HomeSeerEntityBase
from .helpers import (
    is_plain_sensor,
    is_excluded,
    sensor_device_class,
    unit_of_measurement,
)
from .bridge_stats import ensure_stats, refresh_derived_stats, health_score



async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    state = data["state"]

    refs = [
        ref
        for ref, device in state.items()
        if is_plain_sensor(device) and not is_excluded(device, entry) and not device.get("hide")
    ]

    entities = [
        HomeSeerSensor(entry, ref, device)
        for ref in refs
        for device in [state[ref]]
    ]

entities.extend(
    HomeSeerBridgeMonitorSensor(entry, key, name, unit)
    for key, name, unit in MONITOR_SENSORS
)

data.setdefault("entity_adders", {})["sensor"] = async_add_entities
data.setdefault("known_entity_refs", {}).setdefault("sensor", set()).update(refs)
async_add_entities(entities)


class HomeSeerSensor(HomeSeerEntityBase, SensorEntity):
    def unique_id_for_ref(self, ref: int) -> str:
        return f"homeseer_sensor_{ref}"

    @property
    def native_value(self):
        device = self.device
        value = device.get("numeric_value", device.get("value"))
        if value is None:
            return device.get("status")
        return value

    @property
    def device_class(self):
        return sensor_device_class(self.device)

    @property
    def native_unit_of_measurement(self):
        return unit_of_measurement(self.device)


MONITOR_SENSORS = [
    ("devices_loaded", "HomeSeer Bridge Devices", None),
    ("virtual_devices", "HomeSeer Bridge Virtual Devices", None),
    ("mqtt_updates", "HomeSeer Bridge MQTT Updates", None),
    ("api_refreshes", "HomeSeer Bridge API Refreshes", None),
    ("api_latency_ms", "HomeSeer Bridge API Latency", "ms"),
    ("virtual_polls", "HomeSeer Bridge Virtual Polls", None),
    ("virtual_poll_latency_ms", "HomeSeer Bridge Virtual Poll Latency", "ms"),
    ("last_mqtt_age_seconds", "HomeSeer Bridge Last MQTT Age", "s"),
    ("last_refresh_changed", "HomeSeer Bridge Last Refresh Changes", None),
    ("last_new_devices", "HomeSeer Bridge Last New Devices", None),
    ("total_new_devices_seen", "HomeSeer Bridge New Devices Seen", None),
    ("unmatched_topics", "HomeSeer Bridge Unmatched Topics", None),
    ("health_score", "HomeSeer Bridge Health Score", "%"),
]


class HomeSeerBridgeMonitorSensor(SensorEntity):
    _attr_has_entity_name = False

    def __init__(self, entry, key: str, name: str, unit: str | None):
        self.entry = entry
        self.key = key
        self._attr_name = name
        self._attr_unique_id = f"homeseer_bridge_monitor_{key}"
        self._attr_native_unit_of_measurement = unit

    @property
    def available(self):
        return (
            getattr(self, "hass", None) is not None
            and self.entry.entry_id in self.hass.data.get(DOMAIN, {})
        )

    @property
    def native_value(self):
        data = self.hass.data[DOMAIN][self.entry.entry_id]
        stats = ensure_stats(data)
        refresh_derived_stats(stats)

        if self.key == "devices_loaded":
            return len(data.get("state") or {})
        if self.key == "unmatched_topics":
            return len(data.get("unmatched_topics") or {})
        if self.key == "health_score":
            return health_score(data)

        return stats.get(self.key)

    @property
    def extra_state_attributes(self):
        data = self.hass.data[DOMAIN][self.entry.entry_id]
        stats = ensure_stats(data)
        return {
            "api_healthy": stats.get("last_api_ok"),
            "consecutive_api_failures": stats.get("consecutive_api_failures"),
            "topic_lookup_keys": len(data.get("topic_lookup") or {}),
            "reconnect_attempts": stats.get("reconnect_attempts"),
            "reconnect_successes": stats.get("reconnect_successes"),
        }
