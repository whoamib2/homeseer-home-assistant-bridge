# mcsMQTT Bulk Publishing Setup

mcsMQTT does not expose a documented remote API for enabling outbound
associations. The included utility automates the same database fields used by
the mcsMQTT association editor.

## Important

1. Back up HomeSeer.
2. Stop the mcsMQTT plugin.
3. Run a dry run first.
4. Use `--apply` only after reviewing the generated topics.
5. Restart mcsMQTT afterward.

## Dry run for one ref

```powershell
python .\tools\mcsmqtt_bulk_enable.py `
  --db "C:\Program Files (x86)\HomeSeer HS4\Data\mcsMQTT\mcsMQTT.db" `
  --homeseer-url "http://192.168.0.193" `
  --broker-ip "192.168.0.5" `
  --refs "1359"
```

## Apply for one ref

Add:

```text
--apply
```

## Apply to all supported refs

Leave out `--refs`.

The default `ChangeType` is `7`, which enables:

- Value Change Event
- Value Set Event
- String Change Event

A timestamped database backup is created automatically before any writes.
