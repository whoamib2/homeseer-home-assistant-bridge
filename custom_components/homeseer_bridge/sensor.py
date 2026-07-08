from __future__ import annotations

from homeassistant.components.sensor import SensorEntity

from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import DOMAIN, SIGNAL_NEW_DEVICES
from .entity_base import HomeSeerEntityBase
from .helpers import (
    bridge_device_info,
    is_plain_sensor,
    is_excluded,
    sensor_device_class,
    unit_of_measurement,
)
from .repairs_engine import get_cached_repairs_report
from .bridge_stats import ensure_stats, refresh_derived_stats, health_score, live_device_stats, smart_model_stats, area_floor_stats, device_explorer_stats


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
            if not (is_plain_sensor(device) and not is_excluded(device, entry) and not device.get('hide')):
                continue
            entities.append(HomeSeerSensor(entry, ref, device))
            known_refs.add(ref)
        return entities

    entities = build_entities(list(state.keys()))

    entities.extend(
        HomeSeerBridgeMonitorSensor(entry, key, name, unit)
        for key, name, unit in MONITOR_SENSORS
    )
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


class HomeSeerSensor(HomeSeerEntityBase, SensorEntity):
    def unique_id_for_ref(self, ref: int) -> str:
        return f"homeseer_sensor_{ref}"

    @property
    def native_value(self):
        device = self.device
        value = device.get("numeric_value", device.get("value"))
        if value is None:
            return device.get("status")
        return value

    @property
    def device_class(self):
        return sensor_device_class(self.device)

    @property
    def native_unit_of_measurement(self):
        return unit_of_measurement(self.device)


MONITOR_SENSORS = [
    ("devices_loaded", "HomeSeer Bridge Devices", None),
    ("virtual_devices", "HomeSeer Bridge Virtual Devices", None),
    ("mqtt_updates", "HomeSeer Bridge MQTT Updates", None),
    ("api_refreshes", "HomeSeer Bridge API Refreshes", None),
    ("api_latency_ms", "HomeSeer Bridge API Latency", "ms"),
    ("virtual_polls", "HomeSeer Bridge Virtual Polls", None),
    ("virtual_poll_latency_ms", "HomeSeer Bridge Virtual Poll Latency", "ms"),
    ("last_mqtt_age_seconds", "HomeSeer Bridge Last MQTT Age", "s"),
    ("last_refresh_changed", "HomeSeer Bridge Last Refresh Changes", None),
    ("last_new_devices", "HomeSeer Bridge Last New Devices", None),
    ("total_new_devices_seen", "HomeSeer Bridge New Devices Seen", None),
    ("unmatched_topics", "HomeSeer Bridge Unmatched Topics", None),
    ("health_score", "HomeSeer Bridge Health Score", "%"),
    ("devices_on", "HomeSeer Bridge Devices On", None),
    ("devices_off", "HomeSeer Bridge Devices Off", None),
    ("devices_unknown", "HomeSeer Bridge Devices Unknown", None),
    ("lights_on", "HomeSeer Bridge Lights On", None),
    ("lights_off", "HomeSeer Bridge Lights Off", None),
    ("switches_on", "HomeSeer Bridge Switches On", None),
    ("switches_off", "HomeSeer Bridge Switches Off", None),
    ("binary_sensors_on", "HomeSeer Bridge Binary Sensors On", None),
    ("binary_sensors_off", "HomeSeer Bridge Binary Sensors Off", None),
    ("covers_open", "HomeSeer Bridge Covers Open", None),
    ("covers_closed", "HomeSeer Bridge Covers Closed", None),
    ("locks_unlocked", "HomeSeer Bridge Locks Unlocked", None),
    ("locks_locked", "HomeSeer Bridge Locks Locked", None),
    ("fans_on", "HomeSeer Bridge Fans On", None),
    ("fans_off", "HomeSeer Bridge Fans Off", None),
    ("climate_active", "HomeSeer Bridge Climate Active", None),
    ("low_battery_devices", "HomeSeer Bridge Low Battery Devices", None),
    ("mqtt_updates_per_min", "HomeSeer Bridge MQTT Updates Per Minute", None),
    ("api_refreshes_per_hour", "HomeSeer Bridge API Refreshes Per Hour", None),
    ("virtual_polls_per_min", "HomeSeer Bridge Virtual Polls Per Minute", None),
    ("uptime_seconds", "HomeSeer Bridge Uptime", 's'),
    ("recent_activity", "HomeSeer Bridge Recent Activity", None),
    ("recent_activity_count", "HomeSeer Bridge Recent Activity Count", None),
    ("recent_activity_filtered_count", "HomeSeer Bridge Recent Activity Filtered Count", None),
    ("device_explorer_tracked_refs", "HomeSeer Bridge Explorer Tracked Refs", None),
    ("device_explorer_filtered_refs", "HomeSeer Bridge Explorer Filtered Refs", None),
    ("device_explorer_top_active_count", "HomeSeer Bridge Explorer Top Active Count", None),
    ("device_explorer_top_filtered_count", "HomeSeer Bridge Explorer Top Filtered Count", None),
    ("repairs_total_candidates", "HomeSeer Bridge Repair Candidates", None),
    ("repairs_critical_count", "HomeSeer Bridge Critical Repairs", None),
    ("repairs_warning_count", "HomeSeer Bridge Repair Warnings", None),
    ("repairs_info_count", "HomeSeer Bridge Repair Info", None),
    ("repairs_health_score", "HomeSeer Bridge Repairs Health Score", '%'),
    ("model_lights", "HomeSeer Bridge Model Lights", None),
    ("model_switches", "HomeSeer Bridge Model Switches", None),
    ("model_sensors", "HomeSeer Bridge Model Sensors", None),
    ("model_binary_sensors", "HomeSeer Bridge Model Binary Sensors", None),
    ("model_locks", "HomeSeer Bridge Model Locks", None),
    ("model_covers", "HomeSeer Bridge Model Covers", None),
    ("model_fans", "HomeSeer Bridge Model Fans", None),
    ("model_climate", "HomeSeer Bridge Model Climate", None),
    ("model_other", "HomeSeer Bridge Model Other", None),
    ("model_average_confidence", "HomeSeer Bridge Model Average Confidence", '%'),
    ("area_prep_area_count", "HomeSeer Bridge Proposed Areas", None),
    ("area_prep_floor_count", "HomeSeer Bridge Proposed Floors", None),
    ("area_prep_room_count", "HomeSeer Bridge Proposed Rooms", None),
    ("area_prep_top_area_devices", "HomeSeer Bridge Largest Proposed Area Devices", None),
    ("area_prep_top_floor_devices", "HomeSeer Bridge Largest Proposed Floor Devices", None),
    ("area_apply_last_changed", "HomeSeer Bridge Last Area Apply Changed", None),
    ("area_apply_last_skipped", "HomeSeer Bridge Last Area Apply Skipped", None),
]


MONITOR_SENSOR_OBJECT_IDS = {
    "area_prep_area_count": "homeseer_bridge_proposed_areas",
    "area_prep_floor_count": "homeseer_bridge_proposed_floors",
    "area_prep_room_count": "homeseer_bridge_proposed_rooms",
    "area_prep_top_area_devices": "homeseer_bridge_largest_proposed_area_devices",
    "area_prep_top_floor_devices": "homeseer_bridge_largest_proposed_floor_devices",
    "area_apply_last_changed": "homeseer_bridge_last_area_apply_changed",
    "area_apply_last_skipped": "homeseer_bridge_last_area_apply_skipped",
}

class HomeSeerBridgeMonitorSensor(SensorEntity):
    _attr_has_entity_name = False

    def __init__(self, entry, key: str, name: str, unit: str | None):
        self.entry = entry
        self.key = key
        self._attr_name = name
        self._attr_unique_id = f"homeseer_bridge_monitor_{key}"
        self._attr_suggested_object_id = MONITOR_SENSOR_OBJECT_IDS.get(key)
        self._attr_native_unit_of_measurement = unit


    @property
    def device_info(self):
        return bridge_device_info()

    @property
    def available(self):
        return (
            getattr(self, "hass", None) is not None
            and self.entry.entry_id in self.hass.data.get(DOMAIN, {})
        )

    @property
    def native_value(self):
        data = self.hass.data[DOMAIN][self.entry.entry_id]
        stats = ensure_stats(data)
        refresh_derived_stats(stats)

        if self.key == "devices_loaded":
            return len(data.get("state") or {})
        if self.key == "unmatched_topics":
            return len(data.get("unmatched_topics") or {})
        if self.key == "health_score":
            return health_score(data)
        if self.key == "recent_activity":
            return stats.get("last_activity") or "No recent activity"

        live = live_device_stats(data)
        if self.key in live:
            return live[self.key]

        model_stats = smart_model_stats(data)
        model_map = {
            "model_lights": "light",
            "model_switches": "switch",
            "model_sensors": "sensor",
            "model_binary_sensors": "binary_sensor",
            "model_locks": "lock",
            "model_covers": "cover",
            "model_fans": "fan",
            "model_climate": "climate",
            "model_other": "other",
        }
        if self.key in model_map:
            return model_stats.get("categories", {}).get(model_map[self.key], 0)
        if self.key == "model_average_confidence":
            return model_stats.get("average_confidence")

        area_stats = area_floor_stats(data)
        if self.key == "area_prep_area_count":
            return area_stats.get("area_count")
        if self.key == "area_prep_floor_count":
            return area_stats.get("floor_count")
        if self.key == "area_prep_room_count":
            return area_stats.get("room_count")
        if self.key == "area_prep_top_area_devices":
            top = area_stats.get("top_areas") or {}
            return next(iter(top.values()), 0)
        if self.key == "area_prep_top_floor_devices":
            top = area_stats.get("top_floors") or {}
            return next(iter(top.values()), 0)
        if self.key == "area_apply_last_changed":
            return stats.get("last_area_apply_changed", 0)
        if self.key == "area_apply_last_skipped":
            return stats.get("last_area_apply_skipped", 0)

        explorer = device_explorer_stats(data)
        if self.key == "device_explorer_tracked_refs":
            return explorer.get("tracked_refs", 0)
        if self.key == "device_explorer_filtered_refs":
            return explorer.get("filtered_tracked_refs", 0)
        if self.key == "device_explorer_top_active_count":
            top = explorer.get("top_active_refs") or []
            return top[0].get("count", 0) if top else 0
        if self.key == "device_explorer_top_filtered_count":
            top = explorer.get("top_filtered_refs") or []
            return top[0].get("count", 0) if top else 0

        report = get_cached_repairs_report(data)
        if self.key == "repairs_total_candidates":
            return report.get("total_candidates", 0)
        if self.key == "repairs_critical_count":
            return report.get("critical_count", 0)
        if self.key == "repairs_warning_count":
            return report.get("warning_count", 0)
        if self.key == "repairs_info_count":
            return report.get("info_count", 0)
        if self.key == "repairs_health_score":
            return report.get("repair_health_score")

        return stats.get(self.key)

    @property
    def extra_state_attributes(self):
        data = self.hass.data[DOMAIN][self.entry.entry_id]
        stats = ensure_stats(data)
        attrs = {
            "api_healthy": stats.get("last_api_ok"),
            "consecutive_api_failures": stats.get("consecutive_api_failures"),
            "topic_lookup_keys": len(data.get("topic_lookup") or {}),
            "reconnect_attempts": stats.get("reconnect_attempts"),
            "reconnect_successes": stats.get("reconnect_successes"),
        }
        if self.key == "recent_activity":
            attrs["events"] = stats.get("recent_activity") or []
            attrs["activity_excluded_terms"] = data.get("activity_excluded_terms") or []
            attrs["filtered_count"] = stats.get("recent_activity_filtered_count", 0)
        if self.key == "model_average_confidence":
            attrs["model_summary"] = smart_model_stats(data)
        if self.key in {
            "area_prep_area_count",
            "area_prep_floor_count",
            "area_prep_room_count",
            "area_prep_top_area_devices",
            "area_prep_top_floor_devices",
        }:
            attrs["area_floor_summary"] = area_floor_stats(data)
        if self.key in {"area_apply_last_changed", "area_apply_last_skipped"}:
            attrs["last_area_apply"] = stats.get("last_area_apply")
        if self.key in {
            "device_explorer_tracked_refs",
            "device_explorer_filtered_refs",
            "device_explorer_top_active_count",
            "device_explorer_top_filtered_count",
        }:
            attrs["device_explorer"] = device_explorer_stats(data)
        if self.key in {
            "repairs_total_candidates",
            "repairs_critical_count",
            "repairs_warning_count",
            "repairs_info_count",
            "repairs_health_score",
        }:
            attrs["repairs_report"] = get_cached_repairs_report(data)
        return attrs
