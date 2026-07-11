# HomeSeer Bridge

## v4.2.1 — MQTT Binary State Fix

- Fixes 0/255 door, motion, contact, and other binary sensors not updating from MQTT.
- Prevents stale HomeSeer API status text from overriding a newer MQTT numeric payload.
- Learns numeric-to-semantic mappings from HomeSeer API value/status pairs.
- Adds binary-state mapping diagnostics and regression tests.


## v4.2.0 — mcsMQTT Bulk Publishing Setup

- Adds a safe companion utility to bulk-enable mcsMQTT outbound publishing.
- Generates topics from HomeSeer floor, room, and feature names.
- Enables Value Change, Value Set, and String Change triggers.
- Supports a dry run, selected refs, exclusions, and automatic timestamped database backups.
- Includes a ready-to-edit example for Ref 1359.


## v4.1.0 — Binary Device Class Intelligence

- Door sensors now display Open/Closed instead of Detected/Clear.
- Window sensors use the native window device class.
- Generic contact sensors use the opening device class.
- Adds metadata-based moisture, smoke, carbon monoxide, gas, tamper, vibration, occupancy, presence, and motion classes.


## v4.0.0 — Metadata-Driven Capabilities

- Adds a HomeSeer CAPI Status/Graphics and Controls capability engine.
- Resolves values such as `22`, `23`, `5632`, and `5633` through HomeSeer status metadata.
- Correctly maps Door/Window values to Open/Closed even when both values are non-zero.
- Detects locks using HomeSeer `DoorLock` and `DoorUnlock` control uses.
- Uses metadata-provided lock command values instead of assuming `0/255`.
- Preserves resolved status source, semantic state, status-pair count, and control-pair count as diagnostics attributes.
- MQTT numeric updates now retain HomeSeer's semantic status instead of replacing it with generic On/Off.


## v3.8.1

- Correctly recognizes HomeSeer/Z-Wave `Door/Window` and contact devices as Home Assistant binary sensors.
- Uses HomeSeer status text before raw numeric values.
- Displays contact devices as Open/Closed instead of values such as 0, 1, 22, or 23.
- Preserves the raw HomeSeer value and status as entity attributes.


A Home Assistant custom integration for **HomeSeer HS4** using the HomeSeer JSON API and **mcsMQTT**.

Designed for large HomeSeer installations with local updates, dashboards, diagnostics, cached analytics, and recorder-safe attributes.

## Features

- Local HomeSeer JSON API discovery and control
- Fast state updates through mcsMQTT
- Lights, switches, sensors, binary sensors, locks, covers, and fans
- Virtual device polling
- Bridge health monitoring
- API latency, MQTT activity, virtual polling, reconnect, and discovery metrics
- Recent Activity and Live Event Viewer dashboard snippets
- Smart Device Model classification
- Auto Area Prep and manual Auto Area Apply
- Device Explorer Prep
- Cached Repairs Prep
- Recorder-safe compact attributes for large installs
- HACS-ready repository structure

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

### Manual installation

Copy:

```text
custom_components/homeseer_bridge
```

to:

```text
/config/custom_components/homeseer_bridge
```

Restart Home Assistant and add the integration from **Settings → Devices & services**.

## Configuration

Typical settings:

```text
HomeSeer URL: http://192.168.0.193
MQTT Prefix: Homeseer/Chip23/mcsMQTT
Excluded terms: august,yolink,shelly
Recent activity excluded terms: utility,jon00
```

## Dashboards

Dashboard snippets are included in the `dashboards/` folder.

Recommended combined file:

```text
dashboards/homeseer_bridge_optional_sections_all.yaml
```

## Diagnostics

Download diagnostics from:

```text
Settings → Devices & services → HomeSeer Bridge → Download diagnostics
```

Full detail reports are kept in diagnostics instead of large sensor attributes.

## HACS publishing

See `docs/HACS_PUBLISHING.md`.

## License

MIT
