from __future__ import annotations

from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import DOMAIN, SIGNAL_STATE_UPDATED
from .helpers import device_info, full_name

class HomeSeerEntityBase:
    _attr_has_entity_name = False

    def __init__(self, entry, ref: int, initial_device: dict):
        self.entry = entry
        self.ref = ref
        self._initial_device = initial_device
        self._attr_name = full_name(initial_device)
        self._attr_unique_id = self.unique_id_for_ref(ref)
        self._attr_device_info = device_info(initial_device)

    @property
    def device(self) -> dict:
        if getattr(self, "hass", None) is None:
            return self._initial_device
        return self.hass.data[DOMAIN][self.entry.entry_id]["state"].get(self.ref, self._initial_device)

    @property
    def available(self) -> bool:
        return bool(self.device)

    async def async_added_to_hass(self):
        signal = f"{SIGNAL_STATE_UPDATED}_{self.entry.entry_id}_{self.ref}"

        def _handle_update():
            self.async_write_ha_state()

        self.async_on_remove(async_dispatcher_connect(self.hass, signal, _handle_update))

    def unique_id_for_ref(self, ref: int) -> str:
        raise NotImplementedError
