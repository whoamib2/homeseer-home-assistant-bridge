from __future__ import annotations

from time import time
from typing import Any

from .bridge_stats import ensure_stats, health_score


DEFAULT_REPAIRS_CACHE_SECONDS = 60


def _candidate(
    repair_id: str,
    severity: str,
    title: str,
    description: str,
    *,
    count: int | None = None,
    refs: list | None = None,
    data: dict | None = None,
) -> dict[str, Any]:
    return {
        "id": repair_id,
        "severity": severity,
        "title": title,
        "description": description,
        "count": count,
        "refs": refs or [],
        "data": data or {},
    }


def _safe_get_cached_report(data: dict) -> dict[str, Any]:
    stats = ensure_stats(data)
    return stats.get("cached_repairs_report") or {
        "generated_at": None,
        "repair_health_score": health_score(data),
        "total_candidates": 0,
        "critical_count": 0,
        "warning_count": 0,
        "info_count": 0,
        "critical": [],
        "warnings": [],
        "info": [],
        "cached": True,
    }


def get_cached_repairs_report(data: dict) -> dict[str, Any]:
    """Return the cached repairs report only.

    This is safe to call from entity properties because it does not scan all
    HomeSeer devices or touch registries.
    """
    return _safe_get_cached_report(data)


def update_cached_repairs_report(data: dict, *, force: bool = False) -> dict[str, Any]:
    """Recompute the repairs report at most once per cache interval.

    This is intentionally lightweight and capped so large HomeSeer installs do
    not block Home Assistant's event loop.
    """
    stats = ensure_stats(data)
    now = time()
    last = stats.get("cached_repairs_report_timestamp")

    if not force and last and now - float(last) < DEFAULT_REPAIRS_CACHE_SECONDS:
        return _safe_get_cached_report(data)

    state = data.get("state") or {}
    unmatched = data.get("unmatched_topics") or {}
    critical: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    info: list[dict[str, Any]] = []

    if not stats.get("last_api_ok", True):
        critical.append(_candidate(
            "api_unhealthy",
            "critical",
            "HomeSeer API unhealthy",
            "The HomeSeer API is currently failing or unreachable.",
            data={"consecutive_failures": stats.get("consecutive_api_failures")},
        ))

    failures = int(stats.get("consecutive_api_failures") or 0)
    if failures >= 3:
        warnings.append(_candidate(
            "api_consecutive_failures",
            "warning",
            "Repeated HomeSeer API failures",
            "The bridge has recorded repeated HomeSeer API failures.",
            count=failures,
        ))

    latency = stats.get("api_latency_ms")
    if isinstance(latency, (int, float)) and latency > 1000:
        warnings.append(_candidate(
            "api_high_latency",
            "warning",
            "High HomeSeer API latency",
            "HomeSeer API responses are slower than expected.",
            data={"api_latency_ms": latency},
        ))

    unmatched_count = len(unmatched)
    if unmatched_count > 0:
        warnings.append(_candidate(
            "unmatched_mqtt_topics",
            "warning",
            "Unmatched MQTT topics",
            "MQTT messages are being received but not matched to HomeSeer refs.",
            count=unmatched_count,
            data={"sample_topics": list(unmatched.keys())[:20]},
        ))

    last_mqtt_age = stats.get("last_mqtt_age_seconds")
    if isinstance(last_mqtt_age, (int, float)) and last_mqtt_age > 3600:
        warnings.append(_candidate(
            "stale_mqtt_activity",
            "warning",
            "MQTT activity is stale",
            "The bridge has not seen a matched MQTT update recently.",
            data={"last_mqtt_age_seconds": last_mqtt_age},
        ))

    # Reuse already-cached/counted explorer data from v3.4.0. Do not rebuild it here.
    filtered_counts = stats.get("filtered_activity_ref_counts") or {}
    active_counts = stats.get("activity_ref_counts") or {}

    top_filtered = sorted(filtered_counts.items(), key=lambda item: item[1], reverse=True)[:20]
    if top_filtered and int(top_filtered[0][1]) >= 10:
        info.append(_candidate(
            "noisy_filtered_refs",
            "info",
            "Noisy filtered activity refs",
            "Some refs are generating many filtered activity events.",
            count=len(top_filtered),
            refs=[ref for ref, _count in top_filtered],
            data={"top_filtered_refs": [{"ref": ref, "count": count} for ref, count in top_filtered]},
        ))

    top_active = sorted(active_counts.items(), key=lambda item: item[1], reverse=True)[:20]
    if top_active and int(top_active[0][1]) >= 25:
        info.append(_candidate(
            "high_activity_refs",
            "info",
            "High activity devices",
            "Some HomeSeer refs are changing frequently.",
            count=len(top_active),
            refs=[ref for ref, _count in top_active],
            data={"top_active_refs": [{"ref": ref, "count": count} for ref, count in top_active]},
        ))

    # Extremely cheap area/category sampling only. Capped to avoid blocking on huge installs.
    missing_area_refs = []
    unknownish_refs = []
    checked = 0
    for ref, device in state.items():
        checked += 1
        if checked > 250:
            break
        text = " ".join(
            str(device.get(key) or "")
            for key in ("name", "location", "location2", "device_type", "device_type_string", "interface", "interface_name")
        ).lower()
        if not (device.get("location") or device.get("location2")):
            missing_area_refs.append(ref)
        if not text.strip() or "unknown" in text:
            unknownish_refs.append(ref)

    if missing_area_refs:
        info.append(_candidate(
            "missing_location_sample",
            "info",
            "Devices missing HomeSeer location data",
            "A sample of devices did not have HomeSeer location/location2 data for area mapping.",
            count=len(missing_area_refs),
            refs=missing_area_refs[:50],
            data={"sampled_devices": checked},
        ))

    if unknownish_refs:
        info.append(_candidate(
            "unknown_device_sample",
            "info",
            "Devices with unknown-looking metadata",
            "A sample of devices had unknown or sparse metadata.",
            count=len(unknownish_refs),
            refs=unknownish_refs[:50],
            data={"sampled_devices": checked},
        ))

    total = len(critical) + len(warnings) + len(info)
    base_health = health_score(data)
    repair_health = max(0, base_health - 30) if critical else max(0, base_health - 10) if warnings else base_health

    report = {
        "generated_at": now,
        "repair_health_score": repair_health,
        "total_candidates": total,
        "critical_count": len(critical),
        "warning_count": len(warnings),
        "info_count": len(info),
        "critical": critical,
        "warnings": warnings,
        "info": info,
        "cached": True,
        "cache_seconds": DEFAULT_REPAIRS_CACHE_SECONDS,
        "sampled_devices": min(len(state), 250),
        "total_devices": len(state),
    }

    stats["cached_repairs_report"] = report
    stats["cached_repairs_report_timestamp"] = now
    stats["repairs_total_candidates"] = total
    stats["repairs_critical_count"] = len(critical)
    stats["repairs_warning_count"] = len(warnings)
    stats["repairs_info_count"] = len(info)
    stats["repairs_health_score"] = repair_health

    return report
