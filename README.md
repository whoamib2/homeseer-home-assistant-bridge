# HomeSeer Home Assistant Bridge

## v1.7.0

- Adds Bridge Monitor sensors for device count, MQTT updates, API refreshes, API latency, virtual polling, new-device discovery, unmatched topics, and health score.
- Adds Bridge Monitor binary sensors for connected/API healthy state.
- Adds lightweight `BridgeStats` helpers used by diagnostics and monitor entities.
- Tracks API refresh latency, virtual poll latency, and last MQTT message age.
- Keeps automatic discovery from v1.6.0 and diagnostics improvements from v1.6.1.


## v1.6.1

- Expands diagnostics with a clearer health summary.
- Adds breakdowns by interface, location, device type, and status.
- Adds virtual-device, new-device, reconnect, API refresh, and MQTT counters to diagnostics.
- Adds samples for virtual refs, unavailable/unknown refs, unmatched MQTT topics, and devices.
- Keeps sensitive config values redacted.


## v1.6.0

- Adds automatic new-device discovery.
- Scheduled HomeSeer API refresh now detects newly added HomeSeer refs.
- When new refs are found, the integration schedules a safe reload so Home Assistant creates the new entities.
- Adds new-device discovery counters in diagnostics stats.
- Keeps MQTT as the instant update path and keeps virtual-device polling from v1.5.2.


## v1.5.2

- Adds hybrid sync for HomeSeer virtual devices that do not publish MQTT.
- Automatically detects likely virtual devices and polls only those devices every 5 seconds by default.
- Adds `virtual_poll_interval_seconds` option; set it to `0` to disable virtual polling.
- Keeps MQTT as the instant update path for physical devices.
- Preserves the v1.5.1 migration fix by keeping config flow version at `1`.


## v1.5.0

- Adds automatic reconnect/backoff checks after HomeSeer API failures.
- Adds redacted diagnostics output for config data and options.
- Adds reconnect statistics to diagnostics.
- Expands options flow with reconnect interval setting.
- Improves local brand icon/logo assets.
- Keeps HACS-compliant metadata from v1.4.0.


## v1.4.0

- Updates `manifest.json` for stricter Home Assistant/HACS validation.
- Simplifies `hacs.json` to the current HACS-compatible minimum.
- Adds local brand assets at `custom_components/homeseer_bridge/brand/icon.png` and `logo.png`.
- Sets code owner and integration type metadata.
- Keeps the v1.3.1 diagnostics fix and v1.3.0 services.


## v1.3.1

- Fixes diagnostics import/setup error.
- Makes diagnostics defensive so it cannot prevent the integration from loading.


## v1.3.0

- Adds Home Assistant services:
  - `homeseer_bridge.refresh_all`
  - `homeseer_bridge.control_device`
  - `homeseer_bridge.reload_devices`
- Adds manual refresh/control/reload counters to diagnostics.
- Manual control immediately updates the local state cache while MQTT confirmation follows.


## v1.2.0

- Adds incremental API refresh to keep HomeSeer and Home Assistant synchronized.
- Default refresh interval is 600 seconds; set to 0 to disable.
- MQTT remains the fast path for instant updates.
- API refresh preserves cached devices if HomeSeer returns a partial response.
- Rebuilds MQTT topic lookup after refresh so renamed/new devices can match.


## v1.1.0

- Includes v1.0.2 thread-safety fix for MQTT-driven updates.
- Adds Home Assistant diagnostics support.
- Tracks recent unmatched MQTT topics for troubleshooting.
- Adds optional debug logging in the integration options.
- Updates repository links to `whoamib2/homeseer-home-assistant-bridge`.
- Shows HomeSeer interface/plugin info in the HA device model where available.


## v1.0.2

- Fixes thread-safety error from MQTT updates.
- Ensures entity state writes run on the Home Assistant event loop.
- Should make MQTT-driven updates apply immediately instead of being delayed or rejected.


## v1.0.1

- Fixes entity setup crash: `NoneType object has no attribute data`.
- Entities no longer access `self.hass` during initialization.


Custom Home Assistant integration for bridging HomeSeer HS4 devices into Home Assistant.

## What it does

- Discovers HomeSeer devices through the HS4 JSON API.
- Uses mcsMQTT topics for state updates.
- Sends commands back to HomeSeer through the HS4 JSON API.
- Supports switches, lights/dimmers, locks, covers, fans, binary sensors, and sensors.
- Supports excluded terms such as `august,yolink,shelly` to avoid duplicating devices already integrated directly in Home Assistant.

## Manual install

Copy:

```text
custom_components/homeseer_bridge
```

to:

```text
/config/custom_components/homeseer_bridge
```

Restart Home Assistant.

Then add:

```text
Settings → Devices & services → Add integration → HomeSeer Bridge
```

Recommended config:

```text
HomeSeer URL: http://192.168.0.193
MQTT Prefix: Homeseer/Chip23/mcsMQTT
Excluded terms: august,yolink,shelly
```

## HACS custom repository install

1. Put this repository on GitHub.
2. In Home Assistant, open HACS.
3. Click the three-dot menu → Custom repositories.
4. Paste the GitHub repo URL.
5. Category: Integration.
6. Install HomeSeer Bridge.
7. Restart Home Assistant.
