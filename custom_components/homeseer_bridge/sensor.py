from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity_base import HomeSeerEntityBase
from .helpers import is_plain_sensor, is_excluded, sensor_device_class, unit_of_measurement

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    state = hass.data[DOMAIN][entry.entry_id]["state"]
    entities = [
        HomeSeerSensor(entry, ref, device)
        for ref, device in state.items()
        if is_plain_sensor(device) and not is_excluded(device, entry) and not device.get("hide")
    ]
    entities.extend(HomeSeerBridgeMonitorSensor(entry, key, name, unit) for key, name, unit in MONITOR_SENSORS)
    async_add_entities(entities)

class HomeSeerSensor(HomeSeerEntityBase, SensorEntity):
    def __init__(self, entry, ref, device):
        super().__init__(entry, ref, device)
        self._attr_device_class = sensor_device_class(self.device)
        self._attr_native_unit_of_measurement = unit_of_measurement(self.device)

    def unique_id_for_ref(self, ref: int) -> str:
        return f"homeseer_bridge_{ref}_sensor"

    @property
    def native_value(self):
        value = self.device.get("numeric_value")
        if value is not None:
            return value
        return self.device.get("status")



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
        return getattr(self, "hass", None) is not None and self.entry.entry_id in self.hass.data.get(DOMAIN, {})

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
        }
