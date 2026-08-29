# Changelog

## v4.3.9

- Removes the bundled installation-specific HomeSeer ref/MQTT topic table.
- Makes name-only MQTT fallback aliases collision-safe by enabling them only for unique names.
- Raises the declared minimum Home Assistant version to 2026.8.0.
- Moves Lovelace from a hard dependency to `after_dependencies`.
- Registers all HomeSeer Bridge custom services as admin-only.
- Redacts credentials embedded in `homeseer_url` from downloadable diagnostics.
- Guards light and fan control against non-numeric HomeSeer CAPI control values.
- Makes the optional generated dashboard admin-only.
- Neutralizes installation-specific values in bundled docs and mcsMQTT utility examples.
- Makes all generated MQTT candidate topics collision-safe, not just name-only aliases.

## v4.3.8

- Uses HomeSeer's `controldevicebylabel` JSON API as the preferred cover-control path.
- Refreshes the exact HomeSeer ref with `everything=true` before control so the bridge can use the authoritative CAPI labels.
- Selects the exact Open/Closed CAPI row rather than relying on value or ControlUse translation.
- Keeps ControlUse and raw value control as compatibility fallbacks.
- Verified against HomeSeer ref 1094, where `label=Open` correctly changes the device to value 100 / state Open.

## v4.3.7

- Uses HomeSeer's `controldevicebycontroluse` endpoint for covers that expose CAPI On/Off control pairs.
- Maps Open to ControlUse On (1) and Close to ControlUse Off (2), which supports virtual devices such as ref 1094 (`0 = Closed`, `100 = Open`).
- Re-reads the exact HomeSeer ref after every cover command and only reports the verified HomeSeer state back to Home Assistant.
- Removes optimistic Open/Closed updates that could make HA appear correct while HomeSeer never changed.
- Raises a Home Assistant error when HomeSeer does not actually reach the requested state.

## v4.3.6

- Makes cover/garage-door commands use HomeSeer CAPI control metadata instead of hard-coded 255/0 values.
- Supports virtual garage-door state devices such as ref 1094 where `0 = Closed` and `100 = Open`.
- Uses ControlUse `On`/`Off` first, then Open/Close labels, with 255/0 only as a compatibility fallback.
- Keeps Home Assistant state synchronized immediately after direct HomeSeer API control.

## v4.3.5

- Removes automatic dashboard creation from integration setup; dashboard creation is now opt-in through `homeseer_bridge.create_dashboard`.
- Replaces direct Lovelace `Store` writes with Lovelace dashboard collection/config APIs and coordinated frontend registration.
- Raises the default full-install virtual polling interval from 5 seconds to 30 seconds.
- Removes installation-specific HomeSeer URL, MQTT prefix, and exclusion-list defaults from new installs.
- Reorders the README so the project description, features, and installation instructions come before release history.

## v4.3.4

- Restores valve/water-valve/pump/siren/appliance classification as controllable switches.
- Uses CAPI ControlUse/Label metadata for actual On and Off command values.
- Fixes reversed devices where 0 means On and 255 means Off.
- Removes the switch-state assumption that every positive numeric value is On.
- Adds valve/control-mapping regression tests.


## v4.3.3

- Adds source-level exclusion before bridge state/topic maps are built.
- Automatically removes excluded devices and their entities from Home Assistant's registry on reload.
- Silently drops MQTT messages belonging to excluded refs instead of recording them as unmatched.
- Adds durable manual device deletion using `ref:<id>` exclusions.
- Adds exclusion cleanup statistics and UltraWeatherWU3/Narrative to new-install defaults.


## v4.3.2

- Fixes battery child features being instantiated as lock entities.
- Centralizes entity-platform selection on `capability_platform()`.
- Preserves native lock classification for real Door Lock child features.


## v4.3.1

- Fixes locks alternating between Unlocked and Unknown.
- Maps HomeSeer Secured/Unsecured status values correctly.
- Preserves the last known lock state during transient value 254 reports.
- Fixes battery and measurement MQTT payloads being treated as binary states.
- Adds lock and battery regression tests.


## v4.3.0

- Adds native Home Assistant sensor device classes, units, and state classes.
- Fixes battery and measurement child features inheriting parent classifications.
- Adds sensor-classification regression tests.


## v4.2.1

- Fixes binary entities remaining in the old state after MQTT 0/255 updates.
- Makes current MQTT numeric payloads authoritative when HomeSeer status text is stale.
- Adds learned value/status mapping and regression tests.


## v4.2.0

- Adds `tools/mcsmqtt_bulk_enable.py` for automated outbound association setup.
- Adds dry-run, selected-ref, exclusion, broker, prefix, and backup support.
- Enables Value Change, Value Set, and String Change events by default.


## v4.1.0

- Adds metadata-priority binary device-class resolution.
- Fixes door/contact devices incorrectly displaying Detected/Clear.
- Adds native door, window, opening, moisture, smoke, carbon monoxide, gas, tamper, vibration, occupancy, presence, and motion classes.


## v4.0.0

- Adds metadata-driven HomeSeer capability engine.
- Translates CAPI Status/Graphics values into semantic Home Assistant states.
- Detects lock controls through DoorLock/DoorUnlock metadata.
- Preserves semantic status during MQTT updates.
- Adds capability diagnostics attributes.


## v3.8.1

- Recognizes `Door/Window`, contact, and opening devices as binary sensors.
- Maps HomeSeer status text and numeric notification values to Home Assistant Open/Closed states.
- Adds raw HomeSeer state attributes for troubleshooting.


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
