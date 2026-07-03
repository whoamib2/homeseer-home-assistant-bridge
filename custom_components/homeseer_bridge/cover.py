from __future__ import annotations

from homeassistant.components.cover import CoverEntity, CoverEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity_base import HomeSeerEntityBase
from .helpers import is_cover, is_excluded

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    state = hass.data[DOMAIN][entry.entry_id]["state"]
    async_add_entities([
        HomeSeerCover(entry, ref)
        for ref, device in state.items()
        if is_cover(device) and not is_excluded(device, entry) and not device.get("hide")
    ])

class HomeSeerCover(HomeSeerEntityBase, CoverEntity):
    _attr_supported_features = CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE

    def unique_id_for_ref(self, ref: int) -> str:
        return f"homeseer_bridge_{ref}_cover"

    @property
    def is_closed(self):
        status = str(self.device.get("status", "")).lower()
        if "closed" in status:
            return True
        if "open" in status:
            return False
        value = self.device.get("numeric_value")
        if value is not None:
            return value == 0
        return None

    async def async_open_cover(self, **kwargs):
        api = self.hass.data[DOMAIN][self.entry.entry_id]["api"]
        await api.async_control_device_by_value(self.ref, 255)
        self.device["numeric_value"] = 255.0
        self.device["status"] = "Open"
        self.async_write_ha_state()

    async def async_close_cover(self, **kwargs):
        api = self.hass.data[DOMAIN][self.entry.entry_id]["api"]
        await api.async_control_device_by_value(self.ref, 0)
        self.device["numeric_value"] = 0.0
        self.device["status"] = "Closed"
        self.async_write_ha_state()
