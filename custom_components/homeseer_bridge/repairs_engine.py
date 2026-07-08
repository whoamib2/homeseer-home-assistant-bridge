from __future__ import annotations

from time import time
from typing import Any

from .bridge_stats import ensure_stats, health_score, device_explorer_stats
from .device_model import classify_device, area_floor_summary


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


def _missing_area_refs(state: dict, limit: int = 50) -> list:
    refs = []
    for ref, device in state.items():
        model = classify_device(device, ref)
        if not model.suggested_area or model.suggested_area == "Unknown":
            refs.append(ref)
        if len(refs) >= limit:
            break
    return refs


def _unknown_category_refs(state: dict, limit: int = 50) -> list:
    refs = []
    for ref, device in state.items():
        model = classify_device(device, ref)
        if model.category == "other" or model.confidence < 50:
            refs.append(ref)
        if len(refs) >= limit:
            break
    return refs


def repairs_report(data: dict) -> dict[str, Any]:
    """Build a safe repair-candidate report.

    This does not create Home Assistant Repair entries yet. It only exposes
    structured candidates through sensors and diagnostics.
    """
    state = data.get("state") or {}
    stats = ensure_stats(data)
    unmatched = data.get("unmatched_topics") or {}
    explorer = device_explorer_stats(data)
    area_summary = area_floor_summary(state)

    critical = []
    warnings = []
    info = []

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

    unknown_refs = _unknown_category_refs(state)
    if unknown_refs:
        info.append(_candidate(
            "unknown_device_category",
            "info",
            "Devices with unknown or low-confidence category",
            "Some HomeSeer devices could not be confidently classified by the Smart Device Model.",
            count=len(unknown_refs),
            refs=unknown_refs,
        ))

    missing_area_refs = _missing_area_refs(state)
    if missing_area_refs:
        info.append(_candidate(
            "missing_proposed_area",
            "info",
            "Devices without proposed area",
            "Some HomeSeer devices do not have enough location data to propose a Home Assistant area.",
            count=len(missing_area_refs),
            refs=missing_area_refs,
        ))

    top_filtered = explorer.get("top_filtered_refs") or []
    if top_filtered:
        noisiest = top_filtered[0]
        if int(noisiest.get("count") or 0) >= 10:
            info.append(_candidate(
                "noisy_filtered_refs",
                "info",
                "Noisy filtered activity refs",
                "Some refs are generating many filtered activity events.",
                count=len(top_filtered),
                refs=[item.get("ref") for item in top_filtered[:20]],
                data={"top_filtered_refs": top_filtered[:20]},
            ))

    top_active = explorer.get("top_active_refs") or []
    if top_active:
        busiest = top_active[0]
        if int(busiest.get("count") or 0) >= 25:
            info.append(_candidate(
                "high_activity_refs",
                "info",
                "High activity devices",
                "Some HomeSeer refs are changing frequently.",
                count=len(top_active),
                refs=[item.get("ref") for item in top_active[:20]],
                data={"top_active_refs": top_active[:20]},
            ))

    total_candidates = len(critical) + len(warnings) + len(info)
    score = health_score(data)
    if critical:
        repair_health = max(0, score - 30)
    elif warnings:
        repair_health = max(0, score - 10)
    else:
        repair_health = score

    report = {
        "generated_at": time(),
        "repair_health_score": repair_health,
        "total_candidates": total_candidates,
        "critical_count": len(critical),
        "warning_count": len(warnings),
        "info_count": len(info),
        "critical": critical,
        "warnings": warnings,
        "info": info,
        "area_summary": {
            "area_count": area_summary.get("area_count"),
            "floor_count": area_summary.get("floor_count"),
            "room_count": area_summary.get("room_count"),
        },
    }

    stats["last_repairs_report"] = report
    stats["repairs_total_candidates"] = total_candidates
    stats["repairs_critical_count"] = len(critical)
    stats["repairs_warning_count"] = len(warnings)
    stats["repairs_info_count"] = len(info)
    stats["repairs_health_score"] = repair_health

    return report
