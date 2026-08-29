from __future__ import annotations

from homeassistant.components.light import LightEntity, ColorMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import DOMAIN, SIGNAL_NEW_DEVICES
from .entity_base import HomeSeerEntityBase
from .helpers import is_dimmer, is_excluded, on_value, off_value

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
            if not (is_dimmer(device) and not is_excluded(device, entry) and not device.get('hide')):
                continue
            entities.append(HomeSeerLight(entry, ref, device))
            known_refs.add(ref)
        return entities

    entities = build_entities(list(state.keys()))
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
        try:
            self.device["numeric_value"] = float(hs_value)
        except (TypeError, ValueError):
            self.device["numeric_value"] = None
        self.device["value"] = hs_value
        self.device["status"] = "On"
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        api = self.hass.data[DOMAIN][self.entry.entry_id]["api"]
        value = off_value(self.device)
        await api.async_control_device_by_value(self.ref, value)
        try:
            self.device["numeric_value"] = float(value)
        except (TypeError, ValueError):
            self.device["numeric_value"] = None
        self.device["value"] = value
        self.device["status"] = "Off"
        self.async_write_ha_state()
