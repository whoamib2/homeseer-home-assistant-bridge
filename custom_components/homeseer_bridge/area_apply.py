from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN
from .device_model import classify_device

_LOGGER = logging.getLogger(__name__)


def _clean(value):
    if value is None:
        return None
    value = str(value).strip()
    return value or None


async def async_apply_suggested_areas(
    hass: HomeAssistant,
    entry_id: str,
    *,
    dry_run: bool = True,
    overwrite: bool = False,
    limit: int | None = None,
) -> dict[str, Any]:
    """Apply previewed HomeSeer suggested areas to HA device registry.

    Safe by default:
    - dry_run=True previews only.
    - overwrite=False skips devices already assigned to an area.
    - only device registry entries with HomeSeer Bridge identifiers are touched.
    """
    data = hass.data.get(DOMAIN, {}).get(entry_id)
    if not data:
        return {"error": "entry_not_loaded", "dry_run": dry_run, "changed": 0, "skipped": 0}

    state = data.get("state") or {}
    area_reg = ar.async_get(hass)
    device_reg = dr.async_get(hass)

    changed: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    created_areas: set[str] = set()

    for ref, device in state.items():
        if limit is not None and len(changed) >= limit:
            break

        model = classify_device(device, ref)
        proposed_area = _clean(model.suggested_area)
        if not proposed_area or proposed_area.lower() == "unknown":
            skipped.append({"ref": ref, "reason": "no_proposed_area"})
            continue

        device_entry = device_reg.async_get_device({(DOMAIN, str(ref))})
        if device_entry is None:
            skipped.append({"ref": ref, "area": proposed_area, "reason": "device_registry_entry_not_found"})
            continue

        if device_entry.area_id and not overwrite:
            skipped.append({
                "ref": ref,
                "area": proposed_area,
                "reason": "already_has_area",
                "existing_area_id": device_entry.area_id,
            })
            continue

        area_entry = area_reg.async_get_area_by_name(proposed_area)
        would_create_area = area_entry is None

        if area_entry is None:
            if dry_run:
                area_id = None
            else:
                area_entry = area_reg.async_create(proposed_area)
                area_id = area_entry.id
                created_areas.add(proposed_area)
        else:
            area_id = area_entry.id

        record = {
            "ref": ref,
            "name": model.name,
            "proposed_area": proposed_area,
            "proposed_floor": model.location2,
            "category": model.category,
            "confidence": model.confidence,
            "device_id": device_entry.id,
            "previous_area_id": device_entry.area_id,
            "would_create_area": would_create_area,
        }

        if not dry_run:
            device_reg.async_update_device(device_entry.id, area_id=area_id)
            record["applied_area_id"] = area_id

        changed.append(record)

    summary = {
        "dry_run": dry_run,
        "overwrite": overwrite,
        "changed": len(changed),
        "skipped": len(skipped),
        "created_areas": sorted(created_areas),
        "changes": changed[:200],
        "skipped_samples": skipped[:100],
    }

    stats = data.setdefault("stats", {})
    stats["last_area_apply"] = summary
    stats["last_area_apply_changed"] = len(changed)
    stats["last_area_apply_skipped"] = len(skipped)
    stats["last_area_apply_dry_run"] = dry_run

    _LOGGER.info(
        "HomeSeer Bridge suggested area apply completed: dry_run=%s overwrite=%s changed=%s skipped=%s",
        dry_run,
        overwrite,
        len(changed),
        len(skipped),
    )

    return summary
