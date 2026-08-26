from __future__ import annotations

import logging
from typing import Any

from homeassistant.components import frontend
from homeassistant.components.lovelace import dashboard
from homeassistant.components.lovelace.const import (
    CONF_ICON,
    CONF_REQUIRE_ADMIN,
    CONF_SHOW_IN_SIDEBAR,
    CONF_TITLE,
    CONF_URL_PATH,
    DOMAIN as LOVELACE_DOMAIN,
    LOVELACE_DATA,
    MODE_STORAGE,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import collection

_LOGGER = logging.getLogger(__name__)

DASHBOARD_URL_PATH = "homeseer-bridge"
DASHBOARD_TITLE = "HomeSeer Bridge"
DASHBOARD_ICON = "mdi:home-automation"


def _dashboard_config() -> dict[str, Any]:
    """Return a modern Sections dashboard config."""
    return {
        "views": [
            {
                "type": "sections",
                "title": "HomeSeer Bridge",
                "path": "homeseer-bridge",
                "icon": DASHBOARD_ICON,
                "sections": [
                    {
                        "type": "grid",
                        "cards": [
                            {"type": "heading", "heading": "HomeSeer Bridge Health"},
                            {"type": "tile", "entity": "binary_sensor.homeseer_bridge_connected", "name": "Bridge Connected", "icon": "mdi:connection"},
                            {"type": "tile", "entity": "binary_sensor.homeseer_bridge_api_healthy", "name": "API Healthy", "icon": "mdi:api"},
                            {"type": "gauge", "entity": "sensor.homeseer_bridge_health_score", "name": "Health Score", "min": 0, "max": 100, "severity": {"green": 90, "yellow": 60, "red": 0}},
                            {"type": "entities", "title": "Health Details", "entities": [
                                {"entity": "sensor.homeseer_bridge_api_latency", "name": "API Latency"},
                                {"entity": "sensor.homeseer_bridge_last_mqtt_age", "name": "Last MQTT Age"},
                                {"entity": "sensor.homeseer_bridge_unmatched_topics", "name": "Unmatched Topics"},
                            ]},
                        ],
                    },
                    {
                        "type": "grid",
                        "cards": [
                            {"type": "heading", "heading": "Device Counts"},
                            {"type": "tile", "entity": "sensor.homeseer_bridge_devices", "name": "Devices", "icon": "mdi:devices"},
                            {"type": "tile", "entity": "sensor.homeseer_bridge_virtual_devices", "name": "Virtual Devices", "icon": "mdi:toggle-switch"},
                            {"type": "entities", "title": "Counts", "entities": [
                                {"entity": "sensor.homeseer_bridge_devices", "name": "Devices"},
                                {"entity": "sensor.homeseer_bridge_virtual_devices", "name": "Virtual Devices"},
                                {"entity": "sensor.homeseer_bridge_unmatched_topics", "name": "Unmatched Topics"},
                            ]},
                        ],
                    },
                    {
                        "type": "grid",
                        "cards": [
                            {"type": "heading", "heading": "Activity"},
                            {"type": "entities", "title": "Bridge Activity", "entities": [
                                {"entity": "sensor.homeseer_bridge_mqtt_updates", "name": "MQTT Updates"},
                                {"entity": "sensor.homeseer_bridge_api_refreshes", "name": "API Refreshes"},
                                {"entity": "sensor.homeseer_bridge_virtual_polls", "name": "Virtual Polls"},
                                {"entity": "sensor.homeseer_bridge_last_refresh_changes", "name": "Last Refresh Changes"},
                                {"entity": "sensor.homeseer_bridge_new_devices_seen", "name": "New Devices Seen"},
                            ]},
                            {"type": "history-graph", "title": "API Latency", "hours_to_show": 24, "entities": ["sensor.homeseer_bridge_api_latency"]},
                            {"type": "history-graph", "title": "Health Score", "hours_to_show": 24, "entities": ["sensor.homeseer_bridge_health_score"]},
                        ],
                    },
                ],
            }
        ]
    }


async def async_ensure_dashboard(hass: HomeAssistant) -> bool:
    """Create the optional dashboard via Lovelace collection/config APIs.

    This is intentionally user-initiated through the create_dashboard service.
    The integration never creates or modifies a dashboard during setup.
    """
    lovelace_data = hass.data.get(LOVELACE_DATA)
    if lovelace_data is None:
        _LOGGER.warning("Lovelace is not loaded; cannot create HomeSeer Bridge dashboard")
        return False

    if DASHBOARD_URL_PATH in lovelace_data.dashboards:
        _LOGGER.debug("HomeSeer Bridge dashboard already exists; not modifying it")
        return False

    dashboards_collection = dashboard.DashboardsCollection(hass)
    await dashboards_collection.async_load()

    for item in dashboards_collection.async_items():
        if item.get(CONF_URL_PATH) == DASHBOARD_URL_PATH or item.get(CONF_TITLE) == DASHBOARD_TITLE:
            _LOGGER.debug("HomeSeer Bridge dashboard already exists in Lovelace storage")
            return False

    async def dashboard_changed(change_type: str, item_id: str, item: dict[str, Any]) -> None:
        """Coordinate the new collection item with the running Lovelace frontend."""
        if change_type != collection.CHANGE_ADDED or item.get(CONF_URL_PATH) != DASHBOARD_URL_PATH:
            return

        storage_dashboard = dashboard.LovelaceStorage(hass, item)
        lovelace_data.dashboards[DASHBOARD_URL_PATH] = storage_dashboard

        if not frontend.async_panel_exists(hass, DASHBOARD_URL_PATH):
            frontend.async_register_built_in_panel(
                hass,
                LOVELACE_DOMAIN,
                frontend_url_path=DASHBOARD_URL_PATH,
                require_admin=item[CONF_REQUIRE_ADMIN],
                show_in_sidebar=item[CONF_SHOW_IN_SIDEBAR],
                sidebar_title=item[CONF_TITLE],
                sidebar_icon=item.get(CONF_ICON, DASHBOARD_ICON),
                config={"mode": MODE_STORAGE},
            )

    remove_listener = dashboards_collection.async_add_listener(dashboard_changed)
    try:
        item = await dashboards_collection.async_create_item(
            {
                CONF_ICON: DASHBOARD_ICON,
                CONF_TITLE: DASHBOARD_TITLE,
                CONF_URL_PATH: DASHBOARD_URL_PATH,
                CONF_SHOW_IN_SIDEBAR: True,
                CONF_REQUIRE_ADMIN: False,
            }
        )
    except HomeAssistantError:
        _LOGGER.exception("Could not create HomeSeer Bridge dashboard entry")
        return False
    finally:
        remove_listener()

    storage_dashboard = lovelace_data.dashboards.get(DASHBOARD_URL_PATH)
    if storage_dashboard is None:
        storage_dashboard = dashboard.LovelaceStorage(hass, item)
        lovelace_data.dashboards[DASHBOARD_URL_PATH] = storage_dashboard

    await storage_dashboard.async_save(_dashboard_config())
    _LOGGER.info("Created HomeSeer Bridge Lovelace dashboard at /%s", DASHBOARD_URL_PATH)
    return True
