from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries

from .const import (
    DOMAIN,
    CONF_HS_URL,
    CONF_MQTT_PREFIX,
    CONF_EXCLUDED_TERMS,
    CONF_ACTIVITY_EXCLUDED_TERMS,
    CONF_ENABLE_DEBUG_LOGGING,
    CONF_REFRESH_INTERVAL_SECONDS,
    CONF_RECONNECT_INTERVAL_SECONDS,
    CONF_VIRTUAL_POLL_INTERVAL_SECONDS,
    DEFAULT_HS_URL,
    DEFAULT_MQTT_PREFIX,
    DEFAULT_EXCLUDED_TERMS,
    DEFAULT_ACTIVITY_EXCLUDED_TERMS,
    DEFAULT_ENABLE_DEBUG_LOGGING,
    DEFAULT_REFRESH_INTERVAL_SECONDS,
    DEFAULT_RECONNECT_INTERVAL_SECONDS,
    DEFAULT_VIRTUAL_POLL_INTERVAL_SECONDS,
)


class HomeSeerBridgeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    @staticmethod
    def async_get_options_flow(config_entry):
        return HomeSeerBridgeOptionsFlow(config_entry)

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            await self.async_set_unique_id("homeseer_bridge")
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title="HomeSeer Bridge", data=user_input)

        schema = vol.Schema({
            vol.Required(CONF_HS_URL, default=DEFAULT_HS_URL): vol.All(str, vol.Length(min=1)),
            vol.Required(CONF_MQTT_PREFIX, default=DEFAULT_MQTT_PREFIX): vol.All(str, vol.Length(min=1)),
            vol.Optional(CONF_EXCLUDED_TERMS, default=DEFAULT_EXCLUDED_TERMS): str,
            vol.Optional(CONF_ACTIVITY_EXCLUDED_TERMS, default=DEFAULT_ACTIVITY_EXCLUDED_TERMS): str,
            vol.Optional(CONF_ENABLE_DEBUG_LOGGING, default=DEFAULT_ENABLE_DEBUG_LOGGING): bool,
            vol.Optional(CONF_REFRESH_INTERVAL_SECONDS, default=DEFAULT_REFRESH_INTERVAL_SECONDS): int,
            vol.Optional(CONF_RECONNECT_INTERVAL_SECONDS, default=DEFAULT_RECONNECT_INTERVAL_SECONDS): int,
            vol.Optional(CONF_VIRTUAL_POLL_INTERVAL_SECONDS, default=DEFAULT_VIRTUAL_POLL_INTERVAL_SECONDS): int,
        })
        return self.async_show_form(step_id="user", data_schema=schema, errors={})


class HomeSeerBridgeOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        data = dict(self._config_entry.data)
        options = dict(self._config_entry.options)

        schema = vol.Schema({
            vol.Optional(
                CONF_MQTT_PREFIX,
                default=options.get(CONF_MQTT_PREFIX, data.get(CONF_MQTT_PREFIX, DEFAULT_MQTT_PREFIX)),
            ): vol.All(str, vol.Length(min=1)),
            vol.Optional(
                CONF_EXCLUDED_TERMS,
                default=options.get(CONF_EXCLUDED_TERMS, data.get(CONF_EXCLUDED_TERMS, DEFAULT_EXCLUDED_TERMS)),
            ): str,
            vol.Optional(
                CONF_ACTIVITY_EXCLUDED_TERMS,
                default=options.get(CONF_ACTIVITY_EXCLUDED_TERMS, data.get(CONF_ACTIVITY_EXCLUDED_TERMS, DEFAULT_ACTIVITY_EXCLUDED_TERMS)),
            ): str,
            vol.Optional(
                CONF_ENABLE_DEBUG_LOGGING,
                default=options.get(CONF_ENABLE_DEBUG_LOGGING, data.get(CONF_ENABLE_DEBUG_LOGGING, DEFAULT_ENABLE_DEBUG_LOGGING)),
            ): bool,
            vol.Optional(
                CONF_REFRESH_INTERVAL_SECONDS,
                default=options.get(CONF_REFRESH_INTERVAL_SECONDS, data.get(CONF_REFRESH_INTERVAL_SECONDS, DEFAULT_REFRESH_INTERVAL_SECONDS)),
            ): int,
            vol.Optional(
                CONF_RECONNECT_INTERVAL_SECONDS,
                default=options.get(CONF_RECONNECT_INTERVAL_SECONDS, data.get(CONF_RECONNECT_INTERVAL_SECONDS, DEFAULT_RECONNECT_INTERVAL_SECONDS)),
            ): int,
            vol.Optional(
                CONF_VIRTUAL_POLL_INTERVAL_SECONDS,
                default=options.get(CONF_VIRTUAL_POLL_INTERVAL_SECONDS, data.get(CONF_VIRTUAL_POLL_INTERVAL_SECONDS, DEFAULT_VIRTUAL_POLL_INTERVAL_SECONDS)),
            ): int,
        })
        return self.async_show_form(step_id="init", data_schema=schema, errors={})
