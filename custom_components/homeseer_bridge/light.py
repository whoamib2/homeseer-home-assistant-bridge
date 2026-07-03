from __future__ import annotations

from homeassistant.components.light import LightEntity, ColorMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity_base import HomeSeerEntityBase
from .helpers import is_dimmer, is_excluded, on_value, off_value

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    state = hass.data[DOMAIN][entry.entry_id]["state"]
    async_add_entities([
        HomeSeerLight(entry, ref)
        for ref, device in state.items()
        if is_dimmer(device) and not is_excluded(device, entry) and not device.get("hide")
    ])

class HomeSeerLight(HomeSeerEntityBase, LightEntity):
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}
    _attr_color_mode = ColorMode.BRIGHTNESS

    def unique_id_for_ref(self, ref: int) -> str:
        return f"homeseer_bridge_{ref}_light"

    @property
    def is_on(self):
        value = self.device.get("numeric_value")
        return value is not None and value > 0

    @property
    def brightness(self):
        value = self.device.get("numeric_value")
        if value is None:
            return None
        if value > 100:
            return 255
        return round((value / 100) * 255)

    async def async_turn_on(self, **kwargs):
        api = self.hass.data[DOMAIN][self.entry.entry_id]["api"]
        brightness = kwargs.get("brightness")
        hs_value = round((brightness / 255) * 100) if brightness is not None else on_value(self.device)
        await api.async_control_device_by_value(self.ref, hs_value)
        self.device["numeric_value"] = float(hs_value)
        self.device["status"] = "On" if hs_value > 0 else "Off"
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        api = self.hass.data[DOMAIN][self.entry.entry_id]["api"]
        value = off_value(self.device)
        await api.async_control_device_by_value(self.ref, value)
        self.device["numeric_value"] = float(value)
        self.device["status"] = "Off"
        self.async_write_ha_state()
