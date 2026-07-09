from __future__ import annotations

from time import time

from .bridge_stats import (
    ensure_stats,
    live_device_stats,
    smart_model_stats,
    area_floor_stats,
    device_explorer_stats,
)
from .repairs_engine import update_cached_repairs_report, get_cached_repairs_report
from .management_engine import update_management_report, get_management_report

CACHE_SECONDS = 60


def _default_cache(data: dict) -> dict:
    stats = ensure_stats(data)
    cache = stats.get("analytics_cache")
    if cache is None:
        cache = {
            "generated_at": None,
            "live": {},
            "model": {"categories": {}, "average_confidence": 0},
            "area": {"area_count": 0, "floor_count": 0, "room_count": 0, "top_areas": {}, "top_floors": {}, "top_rooms": {}},
            "explorer": {"tracked_refs": 0, "filtered_tracked_refs": 0, "top_active_refs": [], "top_filtered_refs": [], "recently_changed_refs": []},
            "repairs": {},
            "management": {},
        }
        stats["analytics_cache"] = cache
    return cache


def get_cached_analytics(data: dict) -> dict:
    return _default_cache(data)


def update_cached_analytics(data: dict, *, force: bool = False) -> dict:
    stats = ensure_stats(data)
    cache = _default_cache(data)
    now = time()
    last = cache.get("generated_at")

    if not force and last and now - float(last) < CACHE_SECONDS:
        return cache

    cache = {
        "generated_at": now,
        "cache_seconds": CACHE_SECONDS,
        "live": live_device_stats(data),
        "model": smart_model_stats(data),
        "area": area_floor_stats(data),
        "explorer": device_explorer_stats(data),
        "repairs": update_cached_repairs_report(data, force=force),
        "management": update_management_report(data, force=force),
    }
    stats["analytics_cache"] = cache
    stats["analytics_cache_timestamp"] = now
    return cache
