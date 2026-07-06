from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity

from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import DOMAIN, SIGNAL_NEW_DEVICES
from .entity_base import HomeSeerEntityBase
from .helpers import bridge_device_info, is_binary_sensor, is_excluded, binary_device_class
from .bridge_stats import ensure_stats, health_score


async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    state = data["state"]
    known_refs = set()

    def build_entities(refs):
        entities = []
        for ref in refs:
            if ref in known_refs:
                continue
            device = state.get(ref)
            if not device:
                continue
            if not (is_binary_sensor(device) and not is_excluded(device, entry) and not device.get('hide')):
                continue
            entities.append(HomeSeerBinarySensor(entry, ref, device))
            known_refs.add(ref)
        return entities

    entities = build_entities(list(state.keys()))

    entities.extend(
    HomeSeerBridgeMonitorBinarySensor(entry, key, name)
        for key, name in MONITOR_BINARY_SENSORS
    )
    async_add_entities(entities)

    def _handle_new_refs(new_refs):
        new_entities = build_entities(new_refs)
        if new_entities:
            data["stats"]["last_new_entities_created"] = len(new_entities)
            data["stats"]["total_new_entities_created"] = data["stats"].get("total_new_entities_created", 0) + len(new_entities)
            async_add_entities(new_entities)

    entry.async_on_unload(
        async_dispatcher_connect(
            hass,
            f"{SIGNAL_NEW_DEVICES}_{entry.entry_id}",
            _handle_new_refs,
        )
    )


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
