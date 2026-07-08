# HomeSeer Bridge Dashboard

For current Home Assistant dashboards using the **Sections** layout, use:

```text
dashboards/homeseer_bridge_sections_view.yaml
```

Paste that YAML into the HomeSeer Bridge dashboard/view configuration.


## v2.7.0 Live Event Viewer

Use this optional dashboard section to show the last 25 HomeSeer changes as a live markdown feed:

```text
dashboards/homeseer_bridge_live_event_viewer_sections.yaml
```

Or use the combined optional sections file:

```text
dashboards/homeseer_bridge_optional_sections_all.yaml
```

The event viewer reads from `sensor.homeseer_bridge_recent_activity` and its `events` attribute.
