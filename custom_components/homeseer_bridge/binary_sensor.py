from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity

from .const import DOMAIN
from .entity_base import HomeSeerEntityBase
from .helpers import bridge_device_info
from .helpers import is_binary_sensor, is_excluded, binary_device_class
from .bridge_stats import ensure_stats, health_score


async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    state = data["state"]

    entities = [
        HomeSeerBinarySensor(entry, ref, device)
        for ref, device in state.items()
        if is_binary_sensor(device) and not is_excluded(device, entry) and not device.get("hide")
    ]

    entities.extend(
        HomeSeerBridgeMonitorBinarySensor(entry, key, name)
        for key, name in MONITOR_BINARY_SENSORS
    )

    async_add_entities(entities)


class HomeSeerBinarySensor(HomeSeerEntityBase, BinarySensorEntity):
    def unique_id_for_ref(self, ref: int) -> str:
        return f"homeseer_binary_sensor_{ref}"

    @property
    def is_on(self):
        device = self.device
        value = device.get("numeric_value", device.get("value"))
        status = str(device.get("status") or "").lower()

        if value is not None:
            try:
                return float(value) != 0
            except (TypeError, ValueError):
                pass

        if status in {"on", "open", "wet", "motion", "detected", "true", "yes", "unlocked"}:
            return True
        if status in {"off", "closed", "dry", "clear", "false", "no", "locked"}:
            return False

        return None

    @property
    def device_class(self):
        return binary_device_class(self.device)


MONITOR_BINARY_SENSORS = [
    ("connected", "HomeSeer Bridge Connected"),
    ("api_healthy", "HomeSeer Bridge API Healthy"),
]


class HomeSeerBridgeMonitorBinarySensor(BinarySensorEntity):
    _attr_has_entity_name = False

    def __init__(self, entry, key: str, name: str):
        self.entry = entry
        self.key = key
        self._attr_name = name
        self._attr_unique_id = f"homeseer_bridge_monitor_{key}"


@property
def device_info(self):
    return bridge_device_info()

    @property
    def available(self):
        return (
            getattr(self, "hass", None) is not None
            and self.entry.entry_id in self.hass.data.get(DOMAIN, {})
        )

    @property
    def is_on(self):
        data = self.hass.data[DOMAIN][self.entry.entry_id]
        stats = ensure_stats(data)

        if self.key == "connected":
            return bool(stats.get("last_api_ok", True)) and health_score(data) >= 50
        if self.key == "api_healthy":
            return bool(stats.get("last_api_ok", True))

        return None

    @property
    def extra_state_attributes(self):
        data = self.hass.data[DOMAIN][self.entry.entry_id]
        stats = ensure_stats(data)
        return {
            "health_score": health_score(data),
            "consecutive_api_failures": stats.get("consecutive_api_failures"),
            "reconnect_attempts": stats.get("reconnect_attempts"),
            "reconnect_successes": stats.get("reconnect_successes"),
        }
