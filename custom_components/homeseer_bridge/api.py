from __future__ import annotations

from urllib.parse import urlencode

class HomeSeerApi:
    def __init__(self, session, base_url: str):
        self.session = session
        self.base_url = base_url.rstrip("/")

    async def async_get_status(self) -> dict[int, dict]:
        url = f"{self.base_url}/JSON?request=getstatus"
        async with self.session.get(url, timeout=30) as resp:
            resp.raise_for_status()
            data = await resp.json(content_type=None)

        devices = {}
        for raw in data.get("Devices", data.get("devices", [])):
            ref = raw.get("ref") or raw.get("Ref") or raw.get("REF")
            if ref is None:
                continue
            try:
                ref = int(ref)
            except Exception:
                continue
            devices[ref] = normalize_device(raw, ref)
        return devices

    async def async_control_device_by_value(self, ref: int, value):
        params = urlencode({"request": "controldevicebyvalue", "ref": ref, "value": value})
        url = f"{self.base_url}/JSON?{params}"
        async with self.session.get(url, timeout=15) as resp:
            resp.raise_for_status()
            try:
                return await resp.json(content_type=None)
            except Exception:
                return await resp.text()

def _first(raw: dict, *keys, default=None):
    for key in keys:
        if key in raw and raw[key] is not None:
            return raw[key]
    return default

def _as_list(value):
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        return list(value.values())
    return []

def _control_pairs(raw: dict):
    for key in (
        "control_pairs", "ControlPairs",
        "CAPIControl", "capi_control",
        "CAPIControls", "capi_controls",
        "ControlPairsDictionary",
    ):
        if key in raw:
            return _as_list(raw[key])
    return []

def _status_pairs(raw: dict):
    for key in (
        "status_graphics", "StatusGraphics",
        "CAPIStatus", "capi_status",
        "CAPIStatusGraphics", "capi_status_graphics",
        "StatusGraphicsDictionary",
    ):
        if key in raw:
            return _as_list(raw[key])
    return []

def _pair_text(pair: dict) -> str:
    if not isinstance(pair, dict):
        return ""
    return " ".join(str(pair.get(k, "")) for k in (
        "Label", "label", "Status", "status", "ControlUse", "control_use",
        "ControlType", "control_type", "Use", "use"
    )).lower()

def _pair_value(pair: dict):
    if not isinstance(pair, dict):
        return None
    for key in ("Value", "value", "Start", "start", "TargetValue", "target_value"):
        if key in pair:
            try:
                return float(pair[key])
            except Exception:
                return pair[key]
    return None

def _flatten_raw(value) -> str:
    parts = []

    def walk(v):
        if isinstance(v, dict):
            for key, val in v.items():
                parts.append(str(key))
                walk(val)
        elif isinstance(v, list):
            for item in v:
                walk(item)
        elif v is not None:
            parts.append(str(v))

    walk(value)
    return " ".join(parts).lower()

def normalize_device(raw: dict, ref: int) -> dict:
    name = _first(raw, "name", "Name", default=f"HomeSeer {ref}")
    location = _first(raw, "location", "Location", default="")
    location2 = _first(raw, "location2", "Location2", default="")
    value = _first(raw, "value", "Value", default=None)
    status = _first(raw, "status", "Status", default="")
    device_type = _first(raw, "device_type_string", "Device_Type_String", "device_type", "DeviceType", default="")
    interface = _first(raw, "interface", "Interface", "interface_name", "Interface_Name", default="")
    relationship = _first(raw, "relationship", "Relationship", default="")
    hide = bool(_first(raw, "hide_from_view", "HideFromView", default=False))
    controls = _control_pairs(raw)
    statuses = _status_pairs(raw)

    try:
        numeric_value = float(value)
    except Exception:
        numeric_value = None

    labels = []
    values = []
    for p in controls + statuses:
        text = _pair_text(p)
        if text:
            labels.append(text)
        val = _pair_value(p)
        if val is not None:
            values.append(val)

    value_status_map = {}
    if numeric_value is not None and status:
        status_lower = str(status).strip().lower()
        inactive_terms = ("closed", "off", "clear", "dry", "no motion", "normal", "idle", "unlocked")
        active_terms = ("open", "on", "detected", "motion", "wet", "alarm", "smoke", "locked", "tamper")
        semantic = None
        if any(term in status_lower for term in inactive_terms):
            semantic = "inactive"
        elif any(term in status_lower for term in active_terms):
            semantic = "active"
        if semantic:
            map_key = str(int(numeric_value) if numeric_value.is_integer() else numeric_value)
            value_status_map[map_key] = semantic

    last_known_lock_state = None
    status_lower_for_lock = str(status or "").strip().lower()
    if "unsecured" in status_lower_for_lock or "unlocked" in status_lower_for_lock:
        last_known_lock_state = "unlocked"
    elif "secured" in status_lower_for_lock or "locked" in status_lower_for_lock:
        last_known_lock_state = "locked"
    elif numeric_value in {0, 1, 16, 17, 32, 33}:
        last_known_lock_state = "unlocked"
    elif numeric_value == 255:
        last_known_lock_state = "locked"

    return {
        "ref": ref,
        "name": str(name),
        "location": str(location or ""),
        "location2": str(location2 or ""),
        "value": value,
        "numeric_value": numeric_value,
        "status": str(status or ""),
        "device_type": str(device_type or ""),
        "interface": str(interface or ""),
        "relationship": str(relationship or ""),
        "hide": hide,
        "controls": controls,
        "statuses": statuses,
        "labels_blob": " ".join(labels),
        "control_values": values,
        "value_status_map": value_status_map,
        "last_known_lock_state": last_known_lock_state,
        "raw_text": _flatten_raw(raw),
        "raw": raw,
    }
