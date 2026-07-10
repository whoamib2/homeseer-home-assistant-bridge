# Changelog

## v3.8.0

- Adds HACS readiness files.
- Adds `hacs.json`.
- Adds `strings.json` and `translations/en.json`.
- Adds GitHub issue templates, PR template, and HACS validation workflow.
- Refreshes README, info, and publishing documentation.
- Updates manifest metadata for documentation, issue tracker, code owners, and HACS friendliness.


## v3.6.1

- Adds cached analytics layer for heavy dashboard calculations.
- Prevents model/area/explorer/repair sensors from scanning all devices during entity state updates.


## v3.6.0

- Adds recorder-safe compact/capped sensor attributes.
- Prevents Auto Area, Device Explorer, Repairs, and Activity sensors from exposing huge attribute payloads.
- Full reports remain available through diagnostics.


## v3.5.4

- Adds explicit suggested object IDs for Auto Area dashboard monitor sensors.


## v3.5.3

- Fixes missing Auto Area Prep/Apply monitor sensors referenced by dashboard YAML.


## v3.5.2

- Adds cached Repairs Prep from stable v3.4.0.
- Avoids expensive repair calculations during sensor state reads.


## v3.4.0

- Adds Device Explorer Prep metrics and diagnostics for active, filtered, and recently changed refs.


## v3.3.0

- Adds Recent Activity filtering with configurable comma-separated terms.
- Adds filtered activity count sensor and diagnostics attributes.


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
