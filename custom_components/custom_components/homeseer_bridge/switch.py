from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity_base import HomeSeerEntityBase
from .helpers import is_controllable_switch, is_excluded, on_value, off_value

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    state = hass.data[DOMAIN][entry.entry_id]["state"]
    async_add_entities([
        HomeSeerSwitch(entry, ref, device)
        for ref, device in state.items()
        if is_controllable_switch(device) and not is_excluded(device, entry)
    ])

class HomeSeerSwitch(HomeSeerEntityBase, SwitchEntity):
    def unique_id_for_ref(self, ref: int) -> str:
        return f"homeseer_bridge_{ref}_switch"

    @property
    def is_on(self):
        value = self.device.get("numeric_value")
        status = str(self.device.get("status", "")).strip().lower()
        if value is not None:
            return value > 0
        return status in ("on", "open", "unlocked", "active")

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
