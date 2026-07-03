from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries

from .const import (
    DOMAIN,
    CONF_HS_URL,
    CONF_MQTT_PREFIX,
    CONF_EXCLUDED_TERMS,
    DEFAULT_HS_URL,
    DEFAULT_MQTT_PREFIX,
    DEFAULT_EXCLUDED_TERMS,
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
            vol.Required(CONF_HS_URL, default=DEFAULT_HS_URL): str,
            vol.Required(CONF_MQTT_PREFIX, default=DEFAULT_MQTT_PREFIX): str,
            vol.Optional(CONF_EXCLUDED_TERMS, default=DEFAULT_EXCLUDED_TERMS): str,
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
            ): str,
            vol.Optional(
                CONF_EXCLUDED_TERMS,
                default=options.get(CONF_EXCLUDED_TERMS, data.get(CONF_EXCLUDED_TERMS, DEFAULT_EXCLUDED_TERMS)),
            ): str,
        })
        return self.async_show_form(step_id="init", data_schema=schema, errors={})
