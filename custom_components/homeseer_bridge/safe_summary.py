from __future__ import annotations

MAX_TOP_ITEMS = 10
MAX_EVENTS = 10
MAX_REFS = 10


def _top_dict(values: dict | None, limit: int = MAX_TOP_ITEMS) -> dict:
    if not values:
        return {}
    return dict(list(values.items())[:limit])


def compact_area_floor_summary(summary: dict | None) -> dict:
    summary = summary or {}
    return {
        "area_count": summary.get("area_count", 0),
        "floor_count": summary.get("floor_count", 0),
        "room_count": summary.get("room_count", 0),
        "top_areas": _top_dict(summary.get("top_areas"), MAX_TOP_ITEMS),
        "top_floors": _top_dict(summary.get("top_floors"), MAX_TOP_ITEMS),
        "top_rooms": _top_dict(summary.get("top_rooms"), MAX_TOP_ITEMS),
        "sample_mappings_count": len(summary.get("sample_mappings") or []),
        "details": "Full mapping is available in downloaded diagnostics.",
    }


def compact_device_explorer_summary(summary: dict | None) -> dict:
    summary = summary or {}

    def trim_entries(entries):
        trimmed = []
        for item in (entries or [])[:MAX_REFS]:
            trimmed.append({
                "ref": item.get("ref"),
                "count": item.get("count"),
                "name": item.get("name"),
                "location": item.get("location"),
                "location2": item.get("location2"),
                "category": item.get("category"),
            })
        return trimmed

    return {
        "tracked_refs": summary.get("tracked_refs", 0),
        "filtered_tracked_refs": summary.get("filtered_tracked_refs", 0),
        "top_active_refs": trim_entries(summary.get("top_active_refs")),
        "top_filtered_refs": trim_entries(summary.get("top_filtered_refs")),
        "recently_changed_refs": trim_entries(summary.get("recently_changed_refs")),
        "details": "Full explorer data is available in downloaded diagnostics.",
    }


def compact_repairs_report(report: dict | None) -> dict:
    report = report or {}

    def trim_candidates(items):
        trimmed = []
        for item in (items or [])[:MAX_TOP_ITEMS]:
            trimmed.append({
                "id": item.get("id"),
                "severity": item.get("severity"),
                "title": item.get("title"),
                "count": item.get("count"),
                "refs": (item.get("refs") or [])[:MAX_REFS],
            })
        return trimmed

    return {
        "generated_at": report.get("generated_at"),
        "repair_health_score": report.get("repair_health_score"),
        "total_candidates": report.get("total_candidates", 0),
        "critical_count": report.get("critical_count", 0),
        "warning_count": report.get("warning_count", 0),
        "info_count": report.get("info_count", 0),
        "critical": trim_candidates(report.get("critical")),
        "warnings": trim_candidates(report.get("warnings")),
        "info": trim_candidates(report.get("info")),
        "cached": report.get("cached"),
        "details": "Full repair data is available in downloaded diagnostics.",
    }


def compact_activity_events(events: list | None) -> list:
    trimmed = []
    for event in (events or [])[:MAX_EVENTS]:
        trimmed.append({
            "timestamp": event.get("timestamp"),
            "ref": event.get("ref"),
            "name": event.get("name"),
            "source": event.get("source"),
            "old": event.get("old"),
            "new": event.get("new"),
        })
    return trimmed


def compact_area_apply(summary: dict | None) -> dict:
    summary = summary or {}
    return {
        "dry_run": summary.get("dry_run"),
        "overwrite": summary.get("overwrite"),
        "changed": summary.get("changed", 0),
        "skipped": summary.get("skipped", 0),
        "created_areas": (summary.get("created_areas") or [])[:MAX_TOP_ITEMS],
        "changes": (summary.get("changes") or [])[:MAX_REFS],
        "skipped_samples": (summary.get("skipped_samples") or [])[:MAX_REFS],
        "details": "Full area apply report is available in downloaded diagnostics.",
    }
