# Changelog

## v3.2.2

- Rebuilt from stable v3.1.1.
- Adds Auto Area Apply service safely.
- Fixes setup handler indentation regression from v3.2.0/v3.2.1.


## v3.1.1

- Documentation refresh.
- Improved README, HACS info text, installation docs, dashboard docs, troubleshooting guide, and roadmap.
- No runtime integration changes.

## v3.1.0

- Adds Auto Area Prep preview layer.
- Exposes proposed Home Assistant area/floor/room mappings from HomeSeer `location2` and `location` fields.
- Adds proposed area/floor/room entity attributes.
- Adds proposed area/floor/room count sensors.
- Safe preview only; does not modify Home Assistant Areas or Floors.

## v3.0.0

- Adds Smart Device Model classification layer.
- Adds classification confidence, suggested area, virtual/battery flags, and category metadata.

## v2.7.x

- Adds Live Event Viewer dashboard YAML.
- Fixes repository LICENSE recognition for HACS.

## v2.6.0

- Adds Recent Activity tracking for MQTT, API refresh, virtual poll, and manual control updates.

## v2.5.1

- Adds Live Device Intelligence from the stable monitor base.

## v2.4.1

- Fixes monitor entities stuck at `unknown`.
