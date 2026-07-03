from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity_base import HomeSeerEntityBase
from .helpers import is_binary_sensor, is_excluded, binary_device_class

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    state = hass.data[DOMAIN][entry.entry_id]["state"]
    async_add_entities([
        HomeSeerBinarySensor(entry, ref)
        for ref, device in state.items()
        if is_binary_sensor(device) and not is_excluded(device, entry) and not device.get("hide")
    ])

class HomeSeerBinarySensor(HomeSeerEntityBase, BinarySensorEntity):
    def __init__(self, entry, ref):
        super().__init__(entry, ref)
        self._attr_device_class = binary_device_class(self.device)

    def unique_id_for_ref(self, ref: int) -> str:
        return f"homeseer_bridge_{ref}_binary_sensor"

    @property
    def is_on(self):
        value = self.device.get("numeric_value")
        status = str(self.device.get("status", "")).strip().lower()
        if value is not None:
            return value > 0
        return status in ("on", "open", "active", "detected", "wet", "unlocked", "tampered")
