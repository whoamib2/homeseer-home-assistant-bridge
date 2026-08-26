from __future__ import annotations

from homeassistant.components.cover import CoverEntity, CoverEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import DOMAIN, SIGNAL_NEW_DEVICES
from .entity_base import HomeSeerEntityBase
from .helpers import is_cover, is_excluded
from .capability_engine import (
    capability_attributes,
    control_value_for_use,
    resolve_status_text,
)


def _control_value_for_label(device: dict, *labels: str):
    """Return a HomeSeer CAPI control value matching one of the labels."""
    wanted = {str(label).strip().lower() for label in labels}
    for pair in device.get("controls") or []:
        if not isinstance(pair, dict):
            continue

        label = ""
        for key in ("Label", "label", "Status", "status", "Text", "text"):
            value = pair.get(key)
            if value is not None and str(value).strip():
                label = str(value).strip().lower()
                break

        if label not in wanted:
            continue

        for key in ("Value", "value", "Start", "start", "TargetValue", "target_value"):
            if key not in pair:
                continue
            try:
                numeric = float(pair[key])
                return int(numeric) if numeric.is_integer() else numeric
            except (TypeError, ValueError):
                return pair[key]
    return None


def cover_open_value(device: dict):
    """Return the actual HomeSeer value used to open this cover.

    HomeSeer virtual garage-door state devices often expose Open as
    ControlUse=On, and the numeric value is not necessarily 255.
    """
    value = control_value_for_use(device, "on", "open")
    if value is None:
        value = _control_value_for_label(device, "open", "opened")
    return 255 if value is None else value


def cover_close_value(device: dict):
    """Return the actual HomeSeer value used to close this cover."""
    value = control_value_for_use(device, "off", "close", "closed")
    if value is None:
        value = _control_value_for_label(device, "close", "closed")
    return 0 if value is None else value


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
            if not (is_cover(device) and not is_excluded(device, entry) and not device.get('hide')):
                continue
            entities.append(HomeSeerCover(entry, ref, device))
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


class HomeSeerCover(HomeSeerEntityBase, CoverEntity):
    _attr_supported_features = CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE

    def unique_id_for_ref(self, ref: int) -> str:
        return f"homeseer_bridge_{ref}_cover"

    @property
    def is_closed(self):
        match = resolve_status_text(self.device)
        text = match.text.lower()
        if "closed" in text:
            return True
        if "open" in text:
            return False
        return None

    @property
    def extra_state_attributes(self):
        attrs = dict(super().extra_state_attributes or {})
        attrs.update(capability_attributes(self.device))
        return attrs

    async def async_open_cover(self, **kwargs):
        api = self.hass.data[DOMAIN][self.entry.entry_id]["api"]
        value = cover_open_value(self.device)
        await api.async_control_device_by_value(self.ref, value)
        try:
            self.device["numeric_value"] = float(value)
        except (TypeError, ValueError):
            self.device["numeric_value"] = None
        self.device["value"] = value
        self.device["status"] = "Open"
        self.async_write_ha_state()

    async def async_close_cover(self, **kwargs):
        api = self.hass.data[DOMAIN][self.entry.entry_id]["api"]
        value = cover_close_value(self.device)
        await api.async_control_device_by_value(self.ref, value)
        try:
            self.device["numeric_value"] = float(value)
        except (TypeError, ValueError):
            self.device["numeric_value"] = None
        self.device["value"] = value
        self.device["status"] = "Closed"
        self.async_write_ha_state()
