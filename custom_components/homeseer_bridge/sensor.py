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
    async_add_entities([
        HomeSeerSensor(entry, ref)
        for ref, device in state.items()
        if is_plain_sensor(device) and not is_excluded(device, entry) and not device.get("hide")
    ])

class HomeSeerSensor(HomeSeerEntityBase, SensorEntity):
    def __init__(self, entry, ref):
        super().__init__(entry, ref)
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
