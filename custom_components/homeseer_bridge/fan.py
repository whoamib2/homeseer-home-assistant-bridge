from __future__ import annotations

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import DOMAIN, SIGNAL_NEW_DEVICES
from .entity_base import HomeSeerEntityBase
from .helpers import is_fan, is_excluded, on_value, off_value

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
            if not (is_fan(device) and not is_excluded(device, entry)):
                continue
            entities.append(HomeSeerFan(entry, ref, device))
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
