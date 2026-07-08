# Dashboard Setup

This integration includes dashboard snippets in the `dashboards/` folder.

For current Home Assistant dashboards using the **Sections** layout, paste snippets into a Sections dashboard view.

## Recommended files

- `homeseer_bridge_sections_view.yaml` — main bridge health dashboard
- `homeseer_bridge_live_intelligence_sections.yaml` — live device counts and performance
- `homeseer_bridge_recent_activity_sections.yaml` — latest activity sensors
- `homeseer_bridge_live_event_viewer_sections.yaml` — last 25 HomeSeer changes
- `homeseer_bridge_smart_device_model_sections.yaml` — classified device counts
- `homeseer_bridge_auto_area_prep_sections.yaml` — proposed area/floor mapping
- `homeseer_bridge_optional_sections_all.yaml` — combined optional sections

## Important

Do not paste a full dashboard YAML file into an individual view editor unless the YAML is view-only. A Sections view should start with:

```yaml
type: sections
sections:
  - type: grid
    cards:
```

If a dashboard appears blank, verify the entity IDs in **Developer Tools → States**.
