#!/usr/bin/env python3
"""Bulk-enable mcsMQTT outbound publishing for HomeSeer devices.

This utility is intentionally separate from the Home Assistant integration.
mcsMQTT does not expose a documented remote write API, so directly editing its
SQLite database from Home Assistant would be unsafe.

The script:
1. Downloads the HomeSeer device list from /JSON?request=getstatus.
2. Creates a timestamped backup of mcsMQTT.db.
3. Creates or updates MQTT_MESSAGE rows.
4. Enables outbound publishing with a generated topic.
5. Enables Value Change, Value Set, and String Change triggers by default.

Run with --dry-run first. Stop the mcsMQTT plugin before using --apply.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
import sys
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


DEFAULT_PREFIX = "Homeseer/Chip23/mcsMQTT"
DEFAULT_CHANGE_TYPE = 7  # 1=value change, 2=value set, 4=string change


def fetch_devices(base_url: str) -> list[dict[str, Any]]:
    url = f"{base_url.rstrip('/')}/JSON?request=getstatus"
    with urllib.request.urlopen(url, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return payload.get("Devices", payload.get("devices", []))


def first(raw: dict, *keys: str, default: Any = "") -> Any:
    for key in keys:
        if key in raw and raw[key] is not None:
            return raw[key]
    return default


def topic_part(value: Any) -> str:
    return str(value or "").strip().replace(" ", "_")


def device_ref(raw: dict) -> int | None:
    value = first(raw, "ref", "Ref", "REF", default=None)
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def device_topic(raw: dict, prefix: str) -> str:
    location2 = topic_part(first(raw, "location2", "Location2"))
    location = topic_part(first(raw, "location", "Location"))
    name = topic_part(first(raw, "name", "Name"))
    parts = [prefix.rstrip("/"), location2, location, name]
    return "/".join(part for part in parts if part)


def should_include(raw: dict, excluded_terms: list[str]) -> bool:
    text = " ".join(
        str(first(raw, key, default=""))
        for key in ("name", "Name", "location", "Location", "location2", "Location2",
                    "interface", "Interface", "device_type", "DeviceType")
    ).lower()
    return not any(term in text for term in excluded_terms)


def ensure_schema(connection: sqlite3.Connection) -> None:
    row = connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='MQTT_MESSAGE'"
    ).fetchone()
    if not row:
        raise RuntimeError("MQTT_MESSAGE table was not found; this is not an mcsMQTT database")


def existing_row(connection: sqlite3.Connection, ref: int):
    return connection.execute(
        "SELECT rowid, * FROM MQTT_MESSAGE WHERE Ref=? ORDER BY rowid LIMIT 1", (ref,)
    ).fetchone()


def update_or_insert(
    connection: sqlite3.Connection,
    *,
    ref: int,
    topic: str,
    broker_ip: str,
    change_type: int,
) -> str:
    row = existing_row(connection, ref)
    if row:
        connection.execute(
            """
            UPDATE MQTT_MESSAGE
               SET Topic=?,
                   Accept=1,
                   Subscribe=0,
                   QOS=0,
                   RetainFlag=0,
                   ChangeType=?,
                   BrokerIP=?,
                   MinSecs=COALESCE(MinSecs, 0),
                   DeadBand=COALESCE(DeadBand, 0),
                   MQTTGROUP=COALESCE(MQTTGROUP, '')
             WHERE rowid=?
            """,
            (topic, change_type, broker_ip, row["rowid"]),
        )
        return "updated"

    connection.execute(
        """
        INSERT INTO MQTT_MESSAGE (
            Source, Topic, Payload, Pattern, Replace, Match, LastDate,
            Reject, Accept, Subscribe, QOS, Ref, RetainFlag, PluginDevice,
            StatusType, History, Template, MISC, Chart, ChangeType, Express,
            Broker, Elevate, URIEncode, ElevateKeys, StorePayload, RefList,
            Energy, VgpMax, Tag, MinSecs, BrokerIP, DeadBand, MQTTGROUP
        ) VALUES (
            '', ?, '', '', '', '0', '',
            0, 1, 0, 0, ?, 0, 0,
            0, 0, '', 4112, 0, ?, 0,
            0, 0, 0, '', 0, '',
            0, 12, '', 0, ?, 0, ''
        )
        """,
        (topic, ref, change_type, broker_ip),
    )
    return "inserted"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True, help="Path to mcsMQTT.db")
    parser.add_argument("--homeseer-url", required=True, help="Example: http://192.168.0.193")
    parser.add_argument("--broker-ip", required=True, help="MQTT broker IP used by mcsMQTT")
    parser.add_argument("--prefix", default=DEFAULT_PREFIX)
    parser.add_argument("--exclude", default="", help="Comma-separated terms to exclude")
    parser.add_argument("--refs", default="", help="Optional comma-separated refs; blank means all")
    parser.add_argument("--change-type", type=int, default=DEFAULT_CHANGE_TYPE)
    parser.add_argument("--apply", action="store_true", help="Actually write changes")
    args = parser.parse_args()

    db_path = Path(args.db).expanduser().resolve()
    if not db_path.exists():
        print(f"Database not found: {db_path}", file=sys.stderr)
        return 2

    selected_refs = {
        int(value.strip()) for value in args.refs.split(",") if value.strip()
    }
    excluded_terms = [
        value.strip().lower() for value in args.exclude.split(",") if value.strip()
    ]

    devices = fetch_devices(args.homeseer_url)
    candidates = []
    for raw in devices:
        ref = device_ref(raw)
        if ref is None:
            continue
        if selected_refs and ref not in selected_refs:
            continue
        if not should_include(raw, excluded_terms):
            continue
        topic = device_topic(raw, args.prefix)
        if topic:
            candidates.append((ref, topic))

    print(f"Found {len(candidates)} candidate HomeSeer devices/features.")
    for ref, topic in candidates[:20]:
        print(f"  {ref}: {topic}")
    if len(candidates) > 20:
        print(f"  ...and {len(candidates) - 20} more")

    if not args.apply:
        print("\nDry run only. Re-run with --apply after stopping the mcsMQTT plugin.")
        return 0

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = db_path.with_name(f"{db_path.name}.backup-{stamp}")
    shutil.copy2(db_path, backup_path)
    print(f"Backup created: {backup_path}")

    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    try:
        ensure_schema(connection)
        inserted = 0
        updated = 0
        with connection:
            for ref, topic in candidates:
                result = update_or_insert(
                    connection,
                    ref=ref,
                    topic=topic,
                    broker_ip=args.broker_ip,
                    change_type=args.change_type,
                )
                if result == "inserted":
                    inserted += 1
                else:
                    updated += 1
        print(f"Completed: {inserted} inserted, {updated} updated.")
    finally:
        connection.close()

    print("Restart the mcsMQTT plugin, then test with Home Assistant MQTT listener.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
