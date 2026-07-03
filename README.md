# HomeSeer Home Assistant Bridge

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
