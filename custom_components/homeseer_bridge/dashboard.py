from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

_LOGGER = logging.getLogger(__name__)

DASHBOARD_ID = "homeseer_bridge"
DASHBOARD_URL_PATH = "homeseer-bridge"
DASHBOARD_TITLE = "HomeSeer Bridge"
DASHBOARD_ICON = "mdi:home-automation"

DASHBOARDS_STORAGE_KEY = "lovelace_dashboards"
DASHBOARD_CONFIG_STORAGE_KEY = f"lovelace.{DASHBOARD_URL_PATH}"


def _dashboard_config() -> dict[str, Any]:
    return {
        "views": [
            {
                "title": "Bridge Health",
                "path": "health",
                "icon": DASHBOARD_ICON,
                "cards": [
                    {
                        "type": "entities",
                        "title": "HomeSeer Bridge Health",
                        "show_header_toggle": False,
                        "entities": [
                            {"entity": "binary_sensor.homeseer_bridge_connected", "name": "Bridge Connected"},
                            {"entity": "binary_sensor.homeseer_bridge_api_healthy", "name": "API Healthy"},
                            {"entity": "sensor.homeseer_bridge_health_score", "name": "Health Score"},
                            {"entity": "sensor.homeseer_bridge_api_latency", "name": "API Latency"},
                            {"entity": "sensor.homeseer_bridge_last_mqtt_age", "name": "Last MQTT Age"},
                        ],
                    },
                    {
                        "type": "entities",
                        "title": "Device Counts",
                        "show_header_toggle": False,
                        "entities": [
                            {"entity": "sensor.homeseer_bridge_devices", "name": "Devices"},
                            {"entity": "sensor.homeseer_bridge_virtual_devices", "name": "Virtual Devices"},
                            {"entity": "sensor.homeseer_bridge_unmatched_topics", "name": "Unmatched Topics"},
                        ],
                    },
                    {
                        "type": "entities",
                        "title": "Activity",
                        "show_header_toggle": False,
                        "entities": [
                            {"entity": "sensor.homeseer_bridge_mqtt_updates", "name": "MQTT Updates"},
                            {"entity": "sensor.homeseer_bridge_api_refreshes", "name": "API Refreshes"},
                            {"entity": "sensor.homeseer_bridge_virtual_polls", "name": "Virtual Polls"},
                            {"entity": "sensor.homeseer_bridge_last_refresh_changes", "name": "Last Refresh Changes"},
                            {"entity": "sensor.homeseer_bridge_new_devices_seen", "name": "New Devices Seen"},
                        ],
                    },
                ],
            }
        ]
    }


async def async_ensure_dashboard(hass: HomeAssistant) -> bool:
    try:
        dashboards_store = Store(hass, 1, DASHBOARDS_STORAGE_KEY)
        dashboards_data = await dashboards_store.async_load() or {"items": []}
        items = dashboards_data.setdefault("items", [])

        for item in items:
            if (
                item.get("url_path") == DASHBOARD_URL_PATH
                or item.get("id") == DASHBOARD_ID
                or item.get("title") == DASHBOARD_TITLE
            ):
                _LOGGER.debug("HomeSeer Bridge dashboard already exists; not modifying it")
                return False

        items.append(
            {
                "id": DASHBOARD_ID,
                "url_path": DASHBOARD_URL_PATH,
                "title": DASHBOARD_TITLE,
                "icon": DASHBOARD_ICON,
                "show_in_sidebar": True,
                "require_admin": False,
                "mode": "storage",
            }
        )

        dashboard_config_store = Store(hass, 1, DASHBOARD_CONFIG_STORAGE_KEY)
        existing_config = await dashboard_config_store.async_load()
        if existing_config is None:
            await dashboard_config_store.async_save(_dashboard_config())

        await dashboards_store.async_save(dashboards_data)
        _LOGGER.info("Created HomeSeer Bridge Lovelace dashboard at /%s", DASHBOARD_URL_PATH)
        return True

    except Exception:
        _LOGGER.exception("Could not create HomeSeer Bridge dashboard")
        return False
