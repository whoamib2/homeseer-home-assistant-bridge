from __future__ import annotations

import logging

from .const import DOMAIN
from .helpers import (
    is_excluded,
    is_controllable_switch,
    is_dimmer,
    is_plain_sensor,
    is_binary_sensor,
    is_lock,
    is_cover,
    is_fan,
)
from .switch import HomeSeerSwitch
from .light import HomeSeerLight
from .sensor import HomeSeerSensor
from .binary_sensor import HomeSeerBinarySensor
from .lock import HomeSeerLock
from .cover import HomeSeerCover
from .fan import HomeSeerFan

_LOGGER = logging.getLogger(__name__)


PLATFORM_FACTORIES = [
    ("switch", HomeSeerSwitch, lambda device, entry: is_controllable_switch(device) and not is_excluded(device, entry)),
    ("light", HomeSeerLight, lambda device, entry: is_dimmer(device) and not is_excluded(device, entry) and not device.get("hide")),
    ("sensor", HomeSeerSensor, lambda device, entry: is_plain_sensor(device) and not is_excluded(device, entry) and not device.get("hide")),
    ("binary_sensor", HomeSeerBinarySensor, lambda device, entry: is_binary_sensor(device) and not is_excluded(device, entry) and not device.get("hide")),
    ("lock", HomeSeerLock, lambda device, entry: is_lock(device) and not is_excluded(device, entry) and not device.get("hide")),
    ("cover", HomeSeerCover, lambda device, entry: is_cover(device) and not is_excluded(device, entry) and not device.get("hide")),
    ("fan", HomeSeerFan, lambda device, entry: is_fan(device) and not is_excluded(device, entry)),
]


async def async_add_new_entities_for_refs(hass, entry, refs: list[int]) -> dict[str, int]:
    """Create Home Assistant entities for newly discovered HomeSeer refs.

    This avoids a full integration reload when HomeSeer adds new devices.
    """
    data = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if not data:
        return {}

    adders = data.setdefault("entity_adders", {})
    known_refs = data.setdefault("known_entity_refs", {})
    state = data.get("state") or {}
    created: dict[str, int] = {}

    for platform, entity_cls, predicate in PLATFORM_FACTORIES:
        add_entities = adders.get(platform)
        if add_entities is None:
            continue

        platform_known = known_refs.setdefault(platform, set())
        entities = []

        for ref in refs:
            if ref in platform_known:
                continue
            device = state.get(ref)
            if not device:
                continue
            if not predicate(device, entry):
                continue

            entities.append(entity_cls(entry, ref, device))
            platform_known.add(ref)

        if entities:
            add_entities(entities)
            created[platform] = len(entities)

    if created:
        _LOGGER.info("HomeSeer Bridge added newly discovered entities without reload: %s", created)

    return created
