from __future__ import annotations

from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import DOMAIN, SIGNAL_STATE_UPDATED
from .bridge_stats import bridge_available
from .helpers import device_info, full_name
from .device_model import model_dict


class HomeSeerEntityBase:
    _attr_has_entity_name = False

    def __init__(self, entry, ref: int, initial_device: dict):
        self.entry = entry
        self.ref = ref
        self._initial_device = initial_device
        self._attr_name = full_name(initial_device)
        self._attr_unique_id = self.unique_id_for_ref(ref)
        self._attr_device_info = device_info(initial_device, ref)

    def _sync_registry_metadata_from_device(self) -> None:
        """Refresh name and device registry metadata from the latest HomeSeer data."""
        device = self.device or self._initial_device
        self._attr_name = full_name(device)
        self._attr_device_info = device_info(device, self.ref)

    @property
    def device(self) -> dict:
        if getattr(self, "hass", None) is None:
            return self._initial_device
        return self.hass.data[DOMAIN][self.entry.entry_id]["state"].get(self.ref, self._initial_device)

    @property
    def available(self) -> bool:
        data = self.hass.data.get(DOMAIN, {}).get(self.entry.entry_id) if getattr(self, "hass", None) else None
        if data is not None and not bridge_available(data):
            return False
        return bool(self.device)

    @property
    def extra_state_attributes(self):
        device = self.device or {}
        model = model_dict(device, self.ref)
        return {
            "homeseer_ref": self.ref,
            "homeseer_location": device.get("location"),
            "homeseer_location2": device.get("location2"),
            "homeseer_interface": device.get("interface") or device.get("interface_name"),
            "homeseer_device_type": device.get("device_type") or device.get("device_type_string"),
            "homeseer_category": model.get("category"),
            "homeseer_category_confidence": model.get("confidence"),
            "homeseer_suggested_area": model.get("suggested_area"),
            "homeseer_is_virtual": model.get("is_virtual"),
            "homeseer_is_battery": model.get("is_battery"),
        }

    async def async_added_to_hass(self):
        self._sync_registry_metadata_from_device()
        signal = f"{SIGNAL_STATE_UPDATED}_{self.entry.entry_id}_{self.ref}"

        def _handle_update():
            self._sync_registry_metadata_from_device()
            self.hass.loop.call_soon_threadsafe(self.async_write_ha_state)

        self.async_on_remove(async_dispatcher_connect(self.hass, signal, _handle_update))

    def unique_id_for_ref(self, ref: int) -> str:
        raise NotImplementedError
