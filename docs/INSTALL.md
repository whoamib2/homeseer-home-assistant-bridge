# Installation

## HACS custom repository

1. Open Home Assistant.
2. Go to **HACS**.
3. Open the three-dot menu.
4. Select **Custom repositories**.
5. Paste the GitHub repository URL.
6. Choose category **Integration**.
7. Install **HomeSeer Bridge**.
8. Restart Home Assistant.
9. Go to **Settings → Devices & services → Add integration → HomeSeer Bridge**.

## Manual installation

Copy:

```text
custom_components/homeseer_bridge
```

to:

```text
/config/custom_components/homeseer_bridge
```

Restart Home Assistant, then add the integration.

## Typical configuration

```text
HomeSeer URL: http://<homeseer-host>:<port>
MQTT Prefix: Homeseer/<your-mcsmqtt-node>/mcsMQTT
Excluded terms: optional comma-separated terms
```

## Notes

- HomeSeer device discovery and control use the HomeSeer JSON API.
- Fast state updates use mcsMQTT.
- Virtual devices can be polled because they may not publish MQTT reliably.
