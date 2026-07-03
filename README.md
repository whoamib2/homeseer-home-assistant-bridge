# HomeSeer Home Assistant Bridge

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
