# Troubleshooting

## Dashboard shows `unknown`

Check **Developer Tools → States** and search:

```text
homeseer_bridge
```

Confirm these exist and have values:

- `binary_sensor.homeseer_bridge_connected`
- `binary_sensor.homeseer_bridge_api_healthy`
- `sensor.homeseer_bridge_health_score`
- `sensor.homeseer_bridge_devices`

If they exist but are unknown, restart Home Assistant and check logs.

## Check logs

```bash
ha core logs | grep -A80 -B20 homeseer_bridge
```

## Download diagnostics

Go to:

```text
Settings → Devices & services → HomeSeer Bridge → Download diagnostics
```

Diagnostics include bridge health, API latency, MQTT activity, virtual poll stats, unmatched topics, recent activity, and Smart Device Model summaries.

## Common issues

### MQTT startup failure

Make sure the MQTT integration is configured and running before HomeSeer Bridge starts.

### Unmatched topics

Check the MQTT prefix and verify mcsMQTT topic structure.

### Virtual devices not updating

Virtual devices may not publish MQTT. The integration includes virtual polling; verify the virtual poll interval is enabled.

### Duplicate devices

Use excluded terms to avoid bridging devices already integrated directly into Home Assistant.
