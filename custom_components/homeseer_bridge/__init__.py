from __future__ import annotations

import logging

from homeassistant.components import mqtt
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .api import HomeSeerApi
from .const import DOMAIN, PLATFORMS, CONF_HS_URL, SIGNAL_STATE_UPDATED, CONF_ENABLE_DEBUG_LOGGING, DEFAULT_ENABLE_DEBUG_LOGGING
from .helpers import apply_mqtt_state, build_topic_lookup, mqtt_prefix, topic_to_ref

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    session = async_get_clientsession(hass)
    api = HomeSeerApi(session, entry.data[CONF_HS_URL])

    # One authoritative central registry. This is the only device state object.
    state = await api.async_get_status()
    topic_lookup = build_topic_lookup(state, entry)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "api": api,
        "state": state,
        "topic_lookup": topic_lookup,
        "unsub": None,
        "unmatched_topics": {},
    }

    wildcard_topic = f"{mqtt_prefix(entry)}/#"
    debug_logging = entry.options.get(CONF_ENABLE_DEBUG_LOGGING, entry.data.get(CONF_ENABLE_DEBUG_LOGGING, DEFAULT_ENABLE_DEBUG_LOGGING))

    @callback
    def mqtt_message_received(msg):
        data = hass.data[DOMAIN][entry.entry_id]
        ref = topic_to_ref(msg.topic, data["topic_lookup"])

        if ref is None:
            unmatched = data.setdefault("unmatched_topics", {})
            unmatched[str(msg.topic)] = str(msg.payload)
            if len(unmatched) > 200:
                # keep diagnostics bounded
                for key in list(unmatched.keys())[:50]:
                    unmatched.pop(key, None)
            if debug_logging:
                _LOGGER.warning("Unmatched HomeSeer MQTT topic: %s payload=%s", msg.topic, msg.payload)
            else:
                _LOGGER.debug("Unmatched HomeSeer MQTT topic: %s payload=%s", msg.topic, msg.payload)
            return

        device = data["state"].get(ref)
        if device is None:
            _LOGGER.debug("Matched MQTT topic to missing HomeSeer ref %s: %s", ref, msg.topic)
            return

        if debug_logging:
            _LOGGER.debug("HomeSeer MQTT update matched ref=%s topic=%s payload=%s", ref, msg.topic, msg.payload)
        apply_mqtt_state(device, msg.payload)
        hass.loop.call_soon_threadsafe(
            async_dispatcher_send,
            hass,
            f"{SIGNAL_STATE_UPDATED}_{entry.entry_id}_{ref}",
        )

    unsub = await mqtt.async_subscribe(hass, wildcard_topic, mqtt_message_received, 0)
    hass.data[DOMAIN][entry.entry_id]["unsub"] = unsub

    _LOGGER.info(
        "HomeSeer Bridge v1.1.0 subscribed to %s with %s devices and %s topic lookup keys",
        wildcard_topic,
        len(state),
        len(topic_lookup),
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_update_options))
    return True

async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    data = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if data and data.get("unsub"):
        data["unsub"]()

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok
