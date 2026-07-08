# HomeSeer Home Assistant Bridge

## v3.5.2

- Built from v3.4.1 Activity Safety Fix.
- Keeps capped/truncated recent activity payloads.
- Adds cached Repairs Prep so sensors never recalculate expensive reports during state reads.
- Repairs report updates at startup and after HomeSeer API refreshes, then sensors read cached values only.


## v3.4.1

- Activity Safety Fix built from stable v3.4.0.
- Caps recent activity history to 10 events.
- Truncates activity names and old/new values to prevent large dashboard payloads.
- Keeps sensor attributes small so the Activity/Live Event Viewer dashboard does not stall Home Assistant.
- No Repairs Prep changes included.


## v3.4.0

- Adds Device Explorer Prep metrics.
- Tracks per-ref visible activity counts.
- Tracks per-ref filtered/noisy activity counts.
- Adds top active refs, top filtered refs, and recently changed refs to sensor attributes and diagnostics.
- Adds Device Explorer Prep dashboard YAML.


## v3.3.0

- Adds Recent Activity filtering.
- New option: `activity_excluded_terms`, defaulting to `utility,jon00`.
- Filters noisy activity events from the Live Event Viewer without removing devices/entities.
- Adds `sensor.homeseer_bridge_recent_activity_filtered_count`.
- Adds activity filter details to diagnostics and sensor attributes.


## v3.2.2

- Rebuilds Auto Area Apply from the stable v3.1.1 base.
- Adds manual `homeseer_bridge.apply_suggested_areas` service.
- Dry-run is enabled by default.
- Skips devices already assigned to an area unless `overwrite: true` is used.
- Fixes the v3.2.0/v3.2.1 setup handler indentation regression.


A custom Home Assistant integration that bridges **HomeSeer HS4** devices into Home Assistant using the HomeSeer JSON API for discovery/control and **mcsMQTT** for fast state updates.

Built for large HomeSeer installations with a focus on speed, diagnostics, visibility, and a polished Home Assistant experience.

## Highlights

- Fast MQTT-driven state updates through mcsMQTT
- HomeSeer JSON API control path
- Supports lights, switches, sensors, binary sensors, locks, covers, fans, and climate-style devices
- Hybrid sync for virtual HomeSeer devices that do not publish MQTT reliably
- Bridge health sensors and binary sensors
- API latency, MQTT activity, virtual polling, reconnect, and discovery metrics
- Rich diagnostics download from Home Assistant
- Dashboard YAML sections for bridge health, live device intelligence, recent activity, live event viewer, smart device modeling, and Auto Area Prep
- Smart Device Model classification layer
- Auto Area Prep preview from HomeSeer `location2` and `location`
- HACS-compatible custom integration structure

## Current features

### Bridge Monitor

Creates monitor entities such as:

- `binary_sensor.homeseer_bridge_connected`
- `binary_sensor.homeseer_bridge_api_healthy`
- `sensor.homeseer_bridge_health_score`
- `sensor.homeseer_bridge_devices`
- `sensor.homeseer_bridge_virtual_devices`
- `sensor.homeseer_bridge_api_latency`
- `sensor.homeseer_bridge_last_mqtt_age`
- `sensor.homeseer_bridge_unmatched_topics`

### Live Device Intelligence

Adds system-wide counts for devices on/off/unknown, lights, switches, covers, locks, fans, low battery devices, MQTT updates/minute, API refreshes/hour, virtual polls/minute, and uptime.

### Recent Activity and Live Event Viewer

Tracks recent HomeSeer changes in:

- `sensor.homeseer_bridge_recent_activity`
- `sensor.homeseer_bridge_recent_activity_count`

Recent events include HomeSeer ref, device name, source, old value, new value, and timestamp.

### Smart Device Model

Classifies HomeSeer devices into:

- light
- switch
- sensor
- binary_sensor
- lock
- cover
- fan
- climate
- other

Entities include troubleshooting attributes for HomeSeer ref, location, interface, device type, proposed category, confidence, suggested area, virtual flag, and battery flag.

### Auto Area Prep

Preview-only mapping from HomeSeer location fields:

- `location2` → proposed floor
- `location` → proposed room
- `location2 + location` → proposed area

This does **not** automatically create or modify Home Assistant Areas or Floors.

## Installation

### HACS custom repository

1. Open Home Assistant.
2. Go to **HACS**.
3. Open the three-dot menu.
4. Select **Custom repositories**.
5. Add this repository URL.
6. Category: **Integration**.
7. Install **HomeSeer Bridge**.
8. Restart Home Assistant.
9. Go to **Settings → Devices & services → Add integration → HomeSeer Bridge**.

### Manual install

Copy:

```text
custom_components/homeseer_bridge
```

to:

```text
/config/custom_components/homeseer_bridge
```

Restart Home Assistant, then add the integration from **Settings → Devices & services**.

## Configuration

Typical settings:

```text
HomeSeer URL: http://192.168.0.193
MQTT Prefix: Homeseer/Chip23/mcsMQTT
Excluded terms: august,yolink,shelly
```

Use excluded terms to avoid duplicating devices already integrated directly into Home Assistant.

## Dashboards

Dashboard snippets are included in `dashboards/`.

Useful files:

- `dashboards/homeseer_bridge_sections_view.yaml`
- `dashboards/homeseer_bridge_live_intelligence_sections.yaml`
- `dashboards/homeseer_bridge_recent_activity_sections.yaml`
- `dashboards/homeseer_bridge_live_event_viewer_sections.yaml`
- `dashboards/homeseer_bridge_smart_device_model_sections.yaml`
- `dashboards/homeseer_bridge_auto_area_prep_sections.yaml`
- `dashboards/homeseer_bridge_optional_sections_all.yaml`

For current Home Assistant dashboards using the **Sections** layout, paste the desired YAML into a Sections dashboard view.

## Services

- `homeseer_bridge.refresh_all`
- `homeseer_bridge.control_device`
- `homeseer_bridge.reload_devices`
- `homeseer_bridge.create_dashboard`

## Diagnostics

Go to:

```text
Settings → Devices & services → HomeSeer Bridge → Download diagnostics
```

Diagnostics include bridge health, API status/latency, MQTT activity, virtual polling, unmatched MQTT topics, recent activity, Smart Device Model summary, Auto Area Prep summary, and sample HomeSeer devices.

## Documentation

- [Installation](docs/INSTALL.md)
- [Dashboard setup](docs/DASHBOARDS.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Roadmap](docs/ROADMAP.md)
- [Changelog](CHANGELOG.md)

## Recommended GitHub About section

Description:

```text
Home Assistant custom integration for HomeSeer HS4 with MQTT updates, diagnostics, smart device modeling, dashboards, and Auto Area Prep.
```

Suggested topics:

```text
home-assistant, homeseer, homeseer-hs4, mqtt, mcsmqtt, hacs, smart-home, home-automation, custom-integration
```

## License

MIT License
