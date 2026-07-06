from __future__ import annotations

from homeassistant.components.lock import LockEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity_base import HomeSeerEntityBase
from .helpers import is_lock, is_excluded


async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    state = data["state"]

    refs = [
        ref
        for ref, device in state.items()
        if is_lock(device) and not is_excluded(device, entry) and not device.get("hide")
    ]

    entities = [
        HomeSeerLock(entry, ref, device)
        for ref in refs
        for device in [state[ref]]
    ]

data.setdefault("entity_adders", {})["lock"] = async_add_entities
data.setdefault("known_entity_refs", {}).setdefault("lock", set()).update(refs)
async_add_entities(entities)


class HomeSeerLock(HomeSeerEntityBase, LockEntity):
    def unique_id_for_ref(self, ref: int) -> str:
        return f"homeseer_bridge_{ref}_lock"

    @property
    def is_locked(self):
        status = str(self.device.get("status", "")).lower()
        value = self.device.get("numeric_value")
        if "unlock" in status:
            return False
        if "lock" in status:
            return True
        if value is not None:
            return value > 0
        return None

    async def async_lock(self, **kwargs):
        api = self.hass.data[DOMAIN][self.entry.entry_id]["api"]
        await api.async_control_device_by_value(self.ref, 255)
        self.device["numeric_value"] = 255.0
        self.device["status"] = "Locked"
        self.async_write_ha_state()

    async def async_unlock(self, **kwargs):
        api = self.hass.data[DOMAIN][self.entry.entry_id]["api"]
        await api.async_control_device_by_value(self.ref, 0)
        self.device["numeric_value"] = 0.0
        self.device["status"] = "Unlocked"
        self.async_write_ha_state()
