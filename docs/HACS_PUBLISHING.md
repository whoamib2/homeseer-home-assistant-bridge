# HACS Publishing Checklist

## Repository

- Public GitHub repository
- `hacs.json`
- `README.md`
- `LICENSE`
- `info.md`
- `custom_components/homeseer_bridge/manifest.json`
- GitHub release tags
- HACS validation workflow passing

## GitHub About section

Description:

```text
Home Assistant custom integration for HomeSeer HS4 with MQTT updates, diagnostics, dashboards, cached analytics, and Auto Area Prep.
```

Topics:

```text
home-assistant, homeseer, homeseer-hs4, mqtt, mcsmqtt, hacs, smart-home, home-automation, custom-integration
```

## Release process

```bash
git tag v3.8.0
git push origin v3.8.0
```

Then create a GitHub Release from the tag and verify HACS validation passes.
