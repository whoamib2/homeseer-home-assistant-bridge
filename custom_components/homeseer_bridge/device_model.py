from __future__ import annotations

from dataclasses import asdict, dataclass
from .sensor_metadata import classify_sensor


@dataclass(frozen=True)
class HomeSeerDeviceModel:
    ref: int | str | None
    name: str
    location: str | None
    location2: str | None
    interface: str | None
    device_type: str | None
    category: str
    confidence: int
    suggested_area: str | None
    is_virtual: bool
    is_battery: bool


def _clean(value):
    if value is None:
        return None
    value = str(value).strip()
    return value or None


def _text(device: dict) -> str:
    return " ".join(
        str(device.get(key) or "")
        for key in (
            "name",
            "location",
            "location2",
            "status",
            "device_type",
            "device_type_string",
            "Device_Type_Description",
            "device_type_description",
            "interface",
            "interface_name",
            "labels_blob",
            "raw_text",
        )
    ).lower()


def _contains_any(text: str, words: tuple[str, ...]) -> bool:
    return any(word in text for word in words)


def classify_device(device: dict, ref=None) -> HomeSeerDeviceModel:
    """Classify one HomeSeer device into a dashboard/diagnostics-friendly model.

    This is intentionally conservative. It does not change the HA platform type yet;
    it provides a stable model for future auto-area, floors, repairs, and explorer work.
    """
    text = _text(device)
    interface = _clean(device.get("interface") or device.get("interface_name"))
    device_type = _clean(
        device.get("device_type_string")
        or device.get("device_type")
        or device.get("Device_Type_Description")
        or device.get("device_type_description")
    )
    hs_ref = device.get("ref") or device.get("Ref") or ref
    name = _clean(device.get("name")) or f"HomeSeer Ref {hs_ref}"

    category = "other"
    confidence = 40

    if _contains_any(text, ("thermostat", "climate", "heating setpoint", "cooling setpoint", "temperature setpoint")):
        category, confidence = "climate", 85
    elif _contains_any(text, ("garage door", "barrier", "cover", "shade", "blind", "curtain")):
        category, confidence = "cover", 85
    elif "lock" in text or "deadbolt" in text:
        category, confidence = "lock", 90
    elif "fan" in text:
        category, confidence = "fan", 80
    elif _contains_any(text, ("motion", "leak", "water sensor", "contact", "door sensor", "window sensor", "door/window", "door window", "smoke", "co sensor", "tamper")):
        category, confidence = "binary_sensor", 85
    elif classify_sensor(device).confidence >= 70:
        sensor_meta = classify_sensor(device)
        category, confidence = "sensor", sensor_meta.confidence
    elif _contains_any(text, ("dimmer", "light", "lamp", "bulb")):
        category, confidence = "light", 85
    elif "switch" in text or "virtual" in text:
        category, confidence = "switch", 70

    is_virtual = bool(
        "virtual" in text
        or "home virtual" in text
        or str(interface or "").lower() in {"virtual", "homeseer"}
    )

    location = _clean(device.get("location"))
    location2 = _clean(device.get("location2"))
    suggested_area = " ".join(part for part in (location2, location) if part) or None

    return HomeSeerDeviceModel(
        ref=hs_ref,
        name=name,
        location=location,
        location2=location2,
        interface=interface,
        device_type=device_type,
        category=category,
        confidence=confidence,
        suggested_area=suggested_area,
        is_virtual=is_virtual,
        is_battery=("battery" in text),
    )


def model_dict(device: dict, ref=None) -> dict:
    return asdict(classify_device(device, ref))


def summarize_models(state: dict) -> dict:
    categories: dict[str, int] = {}
    interfaces: dict[str, int] = {}
    areas: dict[str, int] = {}
    confidence_total = 0
    count = 0

    for ref, device in state.items():
        model = classify_device(device, ref)
        categories[model.category] = categories.get(model.category, 0) + 1
        interfaces[model.interface or "Unknown"] = interfaces.get(model.interface or "Unknown", 0) + 1
        areas[model.suggested_area or "Unknown"] = areas.get(model.suggested_area or "Unknown", 0) + 1
        confidence_total += model.confidence
        count += 1

    return {
        "total": count,
        "categories": dict(sorted(categories.items())),
        "interfaces": dict(sorted(interfaces.items())),
        "areas": dict(sorted(areas.items())),
        "average_confidence": round(confidence_total / count, 1) if count else 0,
    }


def category_count(state: dict, category: str) -> int:
    return sum(1 for ref, device in state.items() if classify_device(device, ref).category == category)
def area_floor_summary(state: dict) -> dict:
    """Summarize proposed Home Assistant area/floor mapping from HomeSeer locations.

    Safe prep only: this does not create or modify HA areas/floors.
    """
    areas: dict[str, int] = {}
    floors: dict[str, int] = {}
    rooms: dict[str, int] = {}
    mappings = []

    for ref, device in state.items():
        model = classify_device(device, ref)
        floor = model.location2 or "Unknown"
        room = model.location or "Unknown"
        area = model.suggested_area or "Unknown"

        floors[floor] = floors.get(floor, 0) + 1
        rooms[room] = rooms.get(room, 0) + 1
        areas[area] = areas.get(area, 0) + 1

        if len(mappings) < 200:
            mappings.append({
                "ref": ref,
                "name": model.name,
                "proposed_floor": floor,
                "proposed_area": area,
                "room": room,
                "category": model.category,
                "confidence": model.confidence,
            })

    def top_items(values: dict[str, int], limit: int = 20):
        return dict(sorted(values.items(), key=lambda item: item[1], reverse=True)[:limit])

    return {
        "area_count": len(areas),
        "floor_count": len(floors),
        "room_count": len(rooms),
        "top_areas": top_items(areas),
        "top_floors": top_items(floors),
        "top_rooms": top_items(rooms),
        "sample_mappings": mappings,
    }
