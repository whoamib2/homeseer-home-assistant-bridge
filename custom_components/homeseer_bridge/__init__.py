from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.components import mqtt
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_track_time_interval

from .api import HomeSeerApi
from .const import (
    DOMAIN,
    PLATFORMS,
    CONF_HS_URL,
    SIGNAL_STATE_UPDATED,
    CONF_ENABLE_DEBUG_LOGGING,
    DEFAULT_ENABLE_DEBUG_LOGGING,
    CONF_REFRESH_INTERVAL_SECONDS,
    DEFAULT_REFRESH_INTERVAL_SECONDS,
)
from .helpers import apply_mqtt_state, build_topic_lookup, mqtt_prefix, topic_to_ref

_LOGGER = logging.getLogger(__name__)


def _device_changed(old: dict | None, new: dict) -> bool:
    if old is None:
        return True

    return (
        old.get("value") != new.get("value")
        or old.get("numeric_value") != new.get("numeric_value")
        or old.get("status") != new.get("status")
        or old.get("name") != new.get("name")
        or old.get("location") != new.get("location")
        or old.get("location2") != new.get("location2")
        or old.get("device_type") != new.get("device_type")
        or old.get("interface") != new.get("interface")
    )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    session = async_get_clientsession(hass)
    api = HomeSeerApi(session, entry.data[CONF_HS_URL])

    state = await api.async_get_status()
    topic_lookup = build_topic_lookup(state, entry)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "api": api,
        "state": state,
        "topic_lookup": topic_lookup,
        "unsub": None,
        "unsub_refresh": None,
        "unmatched_topics": {},
        "stats": {
            "mqtt_updates": 0,
            "api_refreshes": 0,
            "last_refresh_changed": 0,
            "last_refresh_devices": len(state),
        },
    }

    wildcard_topic = f"{mqtt_prefix(entry)}/#"
    debug_logging = entry.options.get(
        CONF_ENABLE_DEBUG_LOGGING,
        entry.data.get(CONF_ENABLE_DEBUG_LOGGING, DEFAULT_ENABLE_DEBUG_LOGGING),
    )

    @callback
    def mqtt_message_received(msg):
        data = hass.data[DOMAIN][entry.entry_id]
        ref = topic_to_ref(msg.topic, data["topic_lookup"])

        if ref is None:
            unmatched = data.setdefault("unmatched_topics", {})
            unmatched[str(msg.topic)] = str(msg.payload)
            if len(unmatched) > 200:
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
        data["stats"]["mqtt_updates"] += 1
        hass.loop.call_soon_threadsafe(
            async_dispatcher_send,
            hass,
            f"{SIGNAL_STATE_UPDATED}_{entry.entry_id}_{ref}",
        )

    unsub = await mqtt.async_subscribe(hass, wildcard_topic, mqtt_message_received, 0)
    hass.data[DOMAIN][entry.entry_id]["unsub"] = unsub

    async def refresh_from_homeseer(now=None):
        data = hass.data.get(DOMAIN, {}).get(entry.entry_id)
        if not data:
            return

        try:
            fresh_state = await api.async_get_status()
        except Exception:
            _LOGGER.exception("HomeSeer Bridge API refresh failed")
            return

        changed_refs: list[int] = []
        current_state = data["state"]

        for ref, new_device in fresh_state.items():
            old_device = current_state.get(ref)
            if _device_changed(old_device, new_device):
                current_state[ref] = new_device
                changed_refs.append(ref)

        # Preserve missing devices so they do not become unavailable from one bad/partial API response.
        # Rebuild topic lookup so renamed/new devices can start matching MQTT.
        data["topic_lookup"] = build_topic_lookup(current_state, entry)
        data["stats"]["api_refreshes"] += 1
        data["stats"]["last_refresh_changed"] = len(changed_refs)
        data["stats"]["last_refresh_devices"] = len(fresh_state)

        if debug_logging:
            _LOGGER.debug(
                "HomeSeer API refresh completed: fresh=%s changed=%s total_cached=%s",
                len(fresh_state),
                len(changed_refs),
                len(current_state),
            )

        for ref in changed_refs:
            hass.loop.call_soon_threadsafe(
                async_dispatcher_send,
                hass,
                f"{SIGNAL_STATE_UPDATED}_{entry.entry_id}_{ref}",
            )

    refresh_interval = int(
        entry.options.get(
            CONF_REFRESH_INTERVAL_SECONDS,
            entry.data.get(CONF_REFRESH_INTERVAL_SECONDS, DEFAULT_REFRESH_INTERVAL_SECONDS),
        )
    )

    if refresh_interval > 0:
        hass.data[DOMAIN][entry.entry_id]["unsub_refresh"] = async_track_time_interval(
            hass,
            refresh_from_homeseer,
            timedelta(seconds=refresh_interval),
        )

    _LOGGER.info(
        "HomeSeer Bridge v1.2.0 subscribed to %s with %s devices, %s topic lookup keys, refresh interval %s seconds",
        wildcard_topic,
        len(state),
        len(topic_lookup),
        refresh_interval,
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
    if data and data.get("unsub_refresh"):
        data["unsub_refresh"]()

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok
