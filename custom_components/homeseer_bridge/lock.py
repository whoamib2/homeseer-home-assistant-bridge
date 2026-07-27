from __future__ import annotations

from homeassistant.components.lock import LockEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import DOMAIN, SIGNAL_NEW_DEVICES
from .entity_base import HomeSeerEntityBase
from .helpers import is_lock, is_excluded
from .capability_engine import lock_state, control_value_for_use, capability_attributes

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
            if not (is_lock(device) and not is_excluded(device, entry) and not device.get('hide')):
                continue
            entities.append(HomeSeerLock(entry, ref, device))
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


class HomeSeerLock(HomeSeerEntityBase, LockEntity):
    def unique_id_for_ref(self, ref: int) -> str:
        return f"homeseer_bridge_{ref}_lock"

    @property
    def is_locked(self):
        state = lock_state(self.device)
        if state in {"locked", "locking", "jammed"}:
            return True
        if state in {"unlocked", "unlocking"}:
            return False
        return None

    @property
    def is_locking(self):
        return lock_state(self.device) == "locking"

    @property
    def is_unlocking(self):
        return lock_state(self.device) == "unlocking"

    @property
    def is_jammed(self):
        return lock_state(self.device) == "jammed"

    @property
    def extra_state_attributes(self):
        attrs = dict(super().extra_state_attributes or {})
        attrs.update(capability_attributes(self.device))
        state = lock_state(self.device)
        if state in {"locked", "unlocked"}:
            self.device["last_known_lock_state"] = state
        attrs["homeseer_lock_state"] = state
        attrs["homeseer_last_known_lock_state"] = self.device.get("last_known_lock_state")
        return attrs

    async def async_lock(self, **kwargs):
        api = self.hass.data[DOMAIN][self.entry.entry_id]["api"]
        value = control_value_for_use(self.device, "doorlock")
        if value is None:
            value = 1
        await api.async_control_device_by_value(self.ref, value)
        self.device["numeric_value"] = float(value)
        self.device["status"] = "Locked"
        self.async_write_ha_state()

    async def async_unlock(self, **kwargs):
        api = self.hass.data[DOMAIN][self.entry.entry_id]["api"]
        value = control_value_for_use(self.device, "doorunlock")
        if value is None:
            value = 0
        await api.async_control_device_by_value(self.ref, value)
        self.device["numeric_value"] = 0.0
        self.device["status"] = "Unlocked"
        self.async_write_ha_state()
