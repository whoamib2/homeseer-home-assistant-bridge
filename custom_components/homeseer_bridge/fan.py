from __future__ import annotations

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity_base import HomeSeerEntityBase
from .helpers import is_fan, is_excluded, on_value, off_value

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    state = hass.data[DOMAIN][entry.entry_id]["state"]
    async_add_entities([
        HomeSeerFan(entry, ref)
        for ref, device in state.items()
        if is_fan(device) and not is_excluded(device, entry) and not device.get("hide")
    ])

class HomeSeerFan(HomeSeerEntityBase, FanEntity):
    _attr_supported_features = FanEntityFeature.TURN_ON | FanEntityFeature.TURN_OFF

    def unique_id_for_ref(self, ref: int) -> str:
        return f"homeseer_bridge_{ref}_fan"

    @property
    def is_on(self):
        value = self.device.get("numeric_value")
        if value is not None:
            return value > 0
        return str(self.device.get("status", "")).lower() == "on"

    async def async_turn_on(self, **kwargs):
        api = self.hass.data[DOMAIN][self.entry.entry_id]["api"]
        value = on_value(self.device)
        await api.async_control_device_by_value(self.ref, value)
        self.device["numeric_value"] = float(value)
        self.device["status"] = "On"
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        api = self.hass.data[DOMAIN][self.entry.entry_id]["api"]
        value = off_value(self.device)
        await api.async_control_device_by_value(self.ref, value)
        self.device["numeric_value"] = float(value)
        self.device["status"] = "Off"
        self.async_write_ha_state()
