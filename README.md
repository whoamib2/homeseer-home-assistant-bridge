# HomeSeer Bridge

HomeSeer Bridge is a Home Assistant custom integration for **HomeSeer HS4**. It combines the HomeSeer JSON API with optional **mcsMQTT** push updates to expose HomeSeer devices as native Home Assistant entities.

It is designed for large HomeSeer installations and focuses on local control, fast state updates, diagnostics, device classification, area suggestions, and recorder-safe monitoring.

## Features

- HomeSeer JSON API discovery and control
- Fast local state updates through mcsMQTT
- Native lights, switches, sensors, binary sensors, locks, covers, and fans
- Metadata-driven Home Assistant device classes and units
- HomeSeer CAPI-aware control values and semantic states
- Configurable source-level exclusions
- Bridge health, latency, reconnect, MQTT, and discovery diagnostics
- Smart Device Model classification
- Auto Area Prep and opt-in Auto Area Apply
- Optional HomeSeer Bridge dashboard, created only when requested
- HACS-ready repository structure

## Requirements

- Home Assistant
- HomeSeer HS4 reachable from Home Assistant
- MQTT configured in Home Assistant if mcsMQTT push updates are used
- mcsMQTT configured to publish the HomeSeer features you want updated in real time

## Installation

### HACS custom repository

1. Open **HACS** in Home Assistant.
2. Open the three-dot menu and choose **Custom repositories**.
3. Add this repository as an **Integration**.
4. Install **HomeSeer Bridge**.
5. Restart Home Assistant.
6. Go to **Settings → Devices & services → Add integration → HomeSeer Bridge**.

### Manual installation

Copy:

```text
custom_components/homeseer_bridge
```

to:

```text
/config/custom_components/homeseer_bridge
```

Restart Home Assistant and add **HomeSeer Bridge** from **Settings → Devices & services**.

## Configuration

The setup form intentionally does not ship with installation-specific addresses, MQTT node names, or exclusion filters.

Example values:

```text
HomeSeer URL: http://<homeseer-host>:<port>
MQTT Prefix: Homeseer/<your-mcsmqtt-node>/mcsMQTT
Excluded terms: optional comma-separated terms
Recent activity excluded terms: optional comma-separated terms
```

The default virtual-device fallback poll interval is **30 seconds**. mcsMQTT remains the preferred path for fast live updates.

## Optional dashboard

The integration does **not** create or modify Lovelace dashboards during setup.

To create the optional HomeSeer Bridge dashboard, run the action:

```text
homeseer_bridge.create_dashboard
```

The dashboard is created through Home Assistant's Lovelace dashboard collection/config APIs and is only created after the user explicitly requests it.

Dashboard YAML examples are also available in the `dashboards/` folder.

## Services / actions

- `homeseer_bridge.refresh_all` — refresh HomeSeer state
- `homeseer_bridge.control_device` — send a raw HomeSeer control value
- `homeseer_bridge.reload_devices` — rebuild the HomeSeer device cache
- `homeseer_bridge.create_dashboard` — opt-in dashboard creation
- `homeseer_bridge.apply_suggested_areas` — preview/apply area suggestions; dry-run is the default

## Diagnostics

Download diagnostics from:

```text
Settings → Devices & services → HomeSeer Bridge → Download diagnostics
```

Full reports are kept in diagnostics instead of large entity attributes.

## Releases

See [CHANGELOG.md](CHANGELOG.md) for release history.

## HACS publishing

See `docs/HACS_PUBLISHING.md`.

## License

MIT
