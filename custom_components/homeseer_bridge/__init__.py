from __future__ import annotations

from datetime import timedelta
import logging
from time import monotonic

import voluptuous as vol

from homeassistant.components import mqtt
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_track_time_interval

from .api import HomeSeerApi
from .const import (
    DOMAIN,
    PLATFORMS,
    CONF_HS_URL,
    SIGNAL_STATE_UPDATED,
    SIGNAL_NEW_DEVICES,
    CONF_ENABLE_DEBUG_LOGGING,
    DEFAULT_ENABLE_DEBUG_LOGGING,
    CONF_REFRESH_INTERVAL_SECONDS,
    DEFAULT_REFRESH_INTERVAL_SECONDS,
    CONF_RECONNECT_INTERVAL_SECONDS,
    DEFAULT_RECONNECT_INTERVAL_SECONDS,
    CONF_VIRTUAL_POLL_INTERVAL_SECONDS,
    DEFAULT_VIRTUAL_POLL_INTERVAL_SECONDS,
)
from .helpers import apply_mqtt_state, build_topic_lookup, mqtt_prefix, topic_to_ref
from .dashboard import async_ensure_dashboard
from .bridge_stats import ensure_stats, mark_mqtt_update, record_latency_ms, refresh_derived_stats, mark_api_refresh, mark_virtual_poll

_LOGGER = logging.getLogger(__name__)

SERVICE_REFRESH_ALL = "refresh_all"
SERVICE_CONTROL_DEVICE = "control_device"
SERVICE_RELOAD_DEVICES = "reload_devices"
SERVICE_CREATE_DASHBOARD = "create_dashboard"


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
        or old.get("device_type_string") != new.get("device_type_string")
        or old.get("interface") != new.get("interface")
        or old.get("interface_name") != new.get("interface_name")
    )


def _is_virtual_device(device: dict) -> bool:
    text = " ".join(
        str(device.get(key) or "")
        for key in (
            "interface",
            "interface_name",
            "device_type",
            "device_type_string",
            "Device_Type_Description",
            "device_type_description",
            "name",
            "location",
            "location2",
        )
    ).lower()

    return (
        "virtual" in text
        or "home virtual" in text
        or str(device.get("interface") or "").lower() in {"virtual", "homeseer"}
        or str(device.get("interface_name") or "").lower() in {"virtual", "homeseer"}
    )


async def _refresh_from_homeseer(hass: HomeAssistant, entry: ConfigEntry, api: HomeSeerApi, debug_logging: bool) -> int:
    data = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if not data:
        return 0

    stats = ensure_stats(data)
    start = monotonic()
    fresh_state = await api.async_get_status()
    record_latency_ms(stats, "api_latency_ms", start)
    mark_api_refresh(stats)
    refresh_derived_stats(stats)
    changed_refs: list[int] = []
    new_refs: list[int] = []
    current_state = data["state"]

    for ref, new_device in fresh_state.items():
        old_device = current_state.get(ref)
        if old_device is None:
            new_refs.append(ref)
        if _device_changed(old_device, new_device):
            current_state[ref] = new_device
            changed_refs.append(ref)

    data["topic_lookup"] = build_topic_lookup(current_state, entry)
    data["virtual_refs"] = {ref for ref, device in current_state.items() if _is_virtual_device(device)}
    data["stats"]["api_refreshes"] += 1
    data["stats"]["last_refresh_changed"] = len(changed_refs)
    data["stats"]["metadata_updates"] = data["stats"].get("metadata_updates", 0) + len(changed_refs)
    data["stats"]["last_refresh_devices"] = len(fresh_state)
    data["stats"]["last_api_ok"] = True
    data["stats"]["consecutive_api_failures"] = 0
    data["stats"]["virtual_devices"] = len(data["virtual_refs"])
    data["stats"]["last_new_devices"] = len(new_refs)
    data["stats"]["total_new_devices_seen"] = data["stats"].get("total_new_devices_seen", 0) + len(new_refs)


    if new_refs:
        data["stats"]["last_new_devices"] = len(new_refs)
        data["stats"]["total_new_devices_seen"] = data["stats"].get("total_new_devices_seen", 0) + len(new_refs)
        _LOGGER.info("HomeSeer Bridge discovered %s new refs; notifying platforms for dynamic entity creation", len(new_refs))
        async_dispatcher_send(hass, f"{SIGNAL_NEW_DEVICES}_{entry.entry_id}", new_refs)

    for ref in changed_refs:
        hass.loop.call_soon_threadsafe(
            async_dispatcher_send, hass, f"{SIGNAL_STATE_UPDATED}_{entry.entry_id}_{ref}"
        )

    return len(changed_refs)


async def _poll_virtual_devices(hass: HomeAssistant, entry: ConfigEntry, api: HomeSeerApi, debug_logging: bool) -> int:
    data = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if not data:
        return 0

    virtual_refs = data.get("virtual_refs") or set()
    if not virtual_refs:
        return 0

    stats = ensure_stats(data)
    start = monotonic()
    fresh_state = await api.async_get_status()
    record_latency_ms(stats, "virtual_poll_latency_ms", start)
    mark_virtual_poll(stats)
    refresh_derived_stats(stats)
    current_state = data["state"]
    changed_refs: list[int] = []

    for ref in virtual_refs:
        new_device = fresh_state.get(ref)
        if new_device is None:
            continue
        old_device = current_state.get(ref)
        if _device_changed(old_device, new_device):
            current_state[ref] = new_device
            changed_refs.append(ref)

    data["stats"]["virtual_polls"] += 1
    data["stats"]["last_virtual_poll_changed"] = len(changed_refs)
    data["stats"]["last_api_ok"] = True
    data["stats"]["consecutive_api_failures"] = 0

    if debug_logging and changed_refs:
        _LOGGER.debug("HomeSeer virtual poll changed refs=%s", changed_refs)

    for ref in changed_refs:
        hass.loop.call_soon_threadsafe(
            async_dispatcher_send, hass, f"{SIGNAL_STATE_UPDATED}_{entry.entry_id}_{ref}"
        )

    return len(changed_refs)



async def _async_reload_for_new_devices(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the config entry after a refresh finds new HomeSeer refs.

    Known refs can be updated immediately, but brand-new refs need a
    config-entry reload so platform setup can create the new entities.
    """
    await hass.config_entries.async_reload(entry.entry_id)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    session = async_get_clientsession(hass)
    api = HomeSeerApi(session, entry.data[CONF_HS_URL])

    state = await api.async_get_status()
    topic_lookup = build_topic_lookup(state, entry)
    virtual_refs = {ref for ref, device in state.items() if _is_virtual_device(device)}

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "api": api,
        "state": state,
        "topic_lookup": topic_lookup,
        "virtual_refs": virtual_refs,
        "unsub": None,
        "unsub_refresh": None,
        "unsub_reconnect_watch": None,
        "unsub_virtual_poll": None,
        "unmatched_topics": {},
        "reload_scheduled": False,
        "stats": {
            "mqtt_updates": 0,
            "api_refreshes": 0,
            "last_refresh_changed": 0,
            "last_refresh_devices": len(state),
            "manual_refreshes": 0,
            "manual_controls": 0,
            "manual_reloads": 0,
            "last_api_ok": True,
            "consecutive_api_failures": 0,
            "reconnect_attempts": 0,
            "reconnect_successes": 0,
            "virtual_devices": len(virtual_refs),
            "virtual_polls": 0,
            "last_virtual_poll_changed": 0,
            "last_new_devices": 0,
            "total_new_devices_seen": 0,
            "last_new_entities_created": 0,
            "total_new_entities_created": 0,
            "metadata_updates": 0,
        },
    }

    ensure_stats(hass.data[DOMAIN][entry.entry_id])
    hass.data[DOMAIN][entry.entry_id]["stats"]["last_api_refresh_timestamp"] = hass.data[DOMAIN][entry.entry_id]["stats"].get("last_api_refresh_timestamp")

    hass.async_create_task(async_ensure_dashboard(hass))

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
        mark_mqtt_update(ensure_stats(data))
        hass.loop.call_soon_threadsafe(
            async_dispatcher_send, hass, f"{SIGNAL_STATE_UPDATED}_{entry.entry_id}_{ref}"
        )

    unsub = await mqtt.async_subscribe(hass, wildcard_topic, mqtt_message_received, 0)
    hass.data[DOMAIN][entry.entry_id]["unsub"] = unsub

    async def refresh_from_homeseer(now=None):
        data = hass.data.get(DOMAIN, {}).get(entry.entry_id)
        if not data:
            return
        try:
            await _refresh_from_homeseer(hass, entry, api, debug_logging)
        except Exception:
            data["stats"]["last_api_ok"] = False
            data["stats"]["consecutive_api_failures"] += 1
            _LOGGER.exception("HomeSeer Bridge API refresh failed")

    refresh_interval = int(entry.options.get(
        CONF_REFRESH_INTERVAL_SECONDS,
        entry.data.get(CONF_REFRESH_INTERVAL_SECONDS, DEFAULT_REFRESH_INTERVAL_SECONDS),
    ))

    if refresh_interval > 0:
        hass.data[DOMAIN][entry.entry_id]["unsub_refresh"] = async_track_time_interval(
            hass, refresh_from_homeseer, timedelta(seconds=refresh_interval)
        )

    virtual_poll_interval = int(entry.options.get(
        CONF_VIRTUAL_POLL_INTERVAL_SECONDS,
        entry.data.get(CONF_VIRTUAL_POLL_INTERVAL_SECONDS, DEFAULT_VIRTUAL_POLL_INTERVAL_SECONDS),
    ))

    async def virtual_poll(now=None):
        data = hass.data.get(DOMAIN, {}).get(entry.entry_id)
        if not data:
            return
        try:
            await _poll_virtual_devices(hass, entry, api, debug_logging)
        except Exception:
            data["stats"]["last_api_ok"] = False
            data["stats"]["consecutive_api_failures"] += 1
            _LOGGER.debug("HomeSeer virtual device poll failed", exc_info=True)

    if virtual_poll_interval > 0 and virtual_refs:
        hass.data[DOMAIN][entry.entry_id]["unsub_virtual_poll"] = async_track_time_interval(
            hass, virtual_poll, timedelta(seconds=virtual_poll_interval)
        )

    reconnect_interval = int(entry.options.get(
        CONF_RECONNECT_INTERVAL_SECONDS,
        entry.data.get(CONF_RECONNECT_INTERVAL_SECONDS, DEFAULT_RECONNECT_INTERVAL_SECONDS),
    ))

    async def reconnect_watch(now=None):
        data = hass.data.get(DOMAIN, {}).get(entry.entry_id)
        if not data:
            return
        if data["stats"].get("last_api_ok", True):
            return
        try:
            data["stats"]["reconnect_attempts"] += 1
            changed = await _refresh_from_homeseer(hass, entry, api, debug_logging)
            data["stats"]["reconnect_successes"] += 1
            _LOGGER.info("HomeSeer Bridge reconnect refresh succeeded; changed refs=%s", changed)
        except Exception:
            data["stats"]["last_api_ok"] = False
            data["stats"]["consecutive_api_failures"] += 1
            _LOGGER.debug("HomeSeer Bridge reconnect check failed", exc_info=True)

    if reconnect_interval > 0:
        hass.data[DOMAIN][entry.entry_id]["unsub_reconnect_watch"] = async_track_time_interval(
            hass, reconnect_watch, timedelta(seconds=reconnect_interval)
        )

    async def handle_refresh_all(call: ServiceCall):
        changed = await _refresh_from_homeseer(hass, entry, api, debug_logging)
        hass.data[DOMAIN][entry.entry_id]["stats"]["manual_refreshes"] += 1
        _LOGGER.info("Manual HomeSeer refresh completed; changed refs=%s", changed)

    async def handle_control_device(call: ServiceCall):
        ref = int(call.data["ref"])
        value = call.data["value"]
        await api.async_control_device_by_value(ref, value)
        data = hass.data[DOMAIN][entry.entry_id]
        data["stats"]["manual_controls"] += 1
        device = data["state"].get(ref)
        if device is not None:
            apply_mqtt_state(device, value)
            hass.loop.call_soon_threadsafe(
                async_dispatcher_send, hass, f"{SIGNAL_STATE_UPDATED}_{entry.entry_id}_{ref}"
            )

    async def handle_create_dashboard(call: ServiceCall):
        created = await async_ensure_dashboard(hass)
        _LOGGER.info("HomeSeer Bridge dashboard create service completed; created=%s", created)

    async def handle_reload_devices(call: ServiceCall):
        fresh_state = await api.async_get_status()
        data = hass.data[DOMAIN][entry.entry_id]
        data["state"].update(fresh_state)
        data["topic_lookup"] = build_topic_lookup(data["state"], entry)
        data["virtual_refs"] = {ref for ref, device in data["state"].items() if _is_virtual_device(device)}
        data["stats"]["manual_reloads"] += 1
        data["stats"]["last_refresh_devices"] = len(fresh_state)
        data["stats"]["virtual_devices"] = len(data["virtual_refs"])
        data["stats"]["last_api_ok"] = True
        data["stats"]["consecutive_api_failures"] = 0
        data["reload_scheduled"] = False
        for ref in fresh_state:
            hass.loop.call_soon_threadsafe(
                async_dispatcher_send, hass, f"{SIGNAL_STATE_UPDATED}_{entry.entry_id}_{ref}"
            )
        _LOGGER.info("Manual HomeSeer device reload completed; devices=%s cached=%s virtual=%s", len(fresh_state), len(data["state"]), len(data["virtual_refs"]))

    if not hass.services.has_service(DOMAIN, SERVICE_REFRESH_ALL):
        hass.services.async_register(DOMAIN, SERVICE_REFRESH_ALL, handle_refresh_all)
    if not hass.services.has_service(DOMAIN, SERVICE_CONTROL_DEVICE):
        hass.services.async_register(
            DOMAIN, SERVICE_CONTROL_DEVICE, handle_control_device,
            schema=vol.Schema({vol.Required("ref"): vol.Coerce(int), vol.Required("value"): object}),
        )
    if not hass.services.has_service(DOMAIN, SERVICE_RELOAD_DEVICES):
        hass.services.async_register(DOMAIN, SERVICE_RELOAD_DEVICES, handle_reload_devices)
    if not hass.services.has_service(DOMAIN, SERVICE_CREATE_DASHBOARD):
        hass.services.async_register(DOMAIN, SERVICE_CREATE_DASHBOARD, handle_create_dashboard)

    _LOGGER.info(
        "HomeSeer Bridge v2.4.0 subscribed to %s with %s devices, %s topic lookup keys, virtual=%s, refresh=%ss virtual_poll=%ss reconnect=%ss",
        wildcard_topic, len(state), len(topic_lookup), len(virtual_refs), refresh_interval, virtual_poll_interval, reconnect_interval
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
    if data and data.get("unsub_reconnect_watch"):
        data["unsub_reconnect_watch"]()
    if data and data.get("unsub_virtual_poll"):
        data["unsub_virtual_poll"]()

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    if not hass.data.get(DOMAIN):
        for service in (SERVICE_REFRESH_ALL, SERVICE_CONTROL_DEVICE, SERVICE_RELOAD_DEVICES, SERVICE_CREATE_DASHBOARD):
            if hass.services.has_service(DOMAIN, service):
                hass.services.async_remove(DOMAIN, service)
    return unload_ok
