from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SensorMetadata:
    device_class: str | None
    unit: str | None
    state_class: str | None
    category: str
    confidence: int


def _clean(value) -> str:
    return " ".join(str(value or "").strip().lower().split())


def identity_text(device: dict) -> str:
    return " ".join(
        _clean(device.get(key))
        for key in (
            "name",
            "device_type",
            "device_type_string",
            "interface",
            "relationship",
            "status",
        )
        if device.get(key) is not None
    )


def _contains(text: str, *terms: str) -> bool:
    return any(term in text for term in terms)


def classify_sensor(device: dict) -> SensorMetadata:
    text = identity_text(device)
    name = _clean(device.get("name"))

    if _contains(name, "battery") or _contains(text, "battery level", "battery percent", "battery"):
        return SensorMetadata("battery", "%", "measurement", "battery", 100)

    if _contains(text, "relative humidity", "humidity", "humid"):
        return SensorMetadata("humidity", "%", "measurement", "humidity", 98)

    if _contains(text, "temperature", "temp sensor", "air temp", "dew point", "heat index"):
        unit = "°C" if _contains(text, "celsius", "°c") else "°F"
        return SensorMetadata("temperature", unit, "measurement", "temperature", 98)

    if _contains(text, "illuminance", "luminance", "light level", "lux"):
        return SensorMetadata("illuminance", "lx", "measurement", "illuminance", 98)

    if _contains(text, "energy", "kwh", "kw hours", "watt hour", "totalpower", "total power"):
        unit = "Wh" if _contains(text, "wh", "watt hour") and "kwh" not in text else "kWh"
        return SensorMetadata("energy", unit, "total_increasing", "energy", 96)

    if _contains(text, "apparent power", "volt amp", " va"):
        return SensorMetadata("apparent_power", "VA", "measurement", "apparent_power", 95)

    if _contains(text, "reactive power", "var"):
        return SensorMetadata("reactive_power", "var", "measurement", "reactive_power", 95)

    if _contains(text, "power factor"):
        return SensorMetadata("power_factor", "%", "measurement", "power_factor", 95)

    if _contains(text, "power", "watts", " watt", "wattage"):
        return SensorMetadata("power", "W", "measurement", "power", 96)

    if _contains(text, "voltage", "volt", "[v]"):
        return SensorMetadata("voltage", "V", "measurement", "voltage", 96)

    if _contains(text, "current", "amps", "ampere", "[a]"):
        return SensorMetadata("current", "A", "measurement", "current", 96)

    if _contains(text, "frequency", "hertz", " hz"):
        return SensorMetadata("frequency", "Hz", "measurement", "frequency", 94)

    if _contains(text, "pressure", "barometric"):
        unit = "inHg" if "inhg" in text else "hPa"
        return SensorMetadata("atmospheric_pressure", unit, "measurement", "pressure", 94)

    if _contains(text, "co2", "carbon dioxide"):
        return SensorMetadata("carbon_dioxide", "ppm", "measurement", "carbon_dioxide", 96)

    if _contains(text, "volatile organic", "voc"):
        return SensorMetadata("volatile_organic_compounds", "µg/m³", "measurement", "voc", 90)

    if _contains(text, "signal strength", "rssi"):
        return SensorMetadata("signal_strength", "dBm", "measurement", "signal_strength", 96)

    if _contains(text, "data rate", "bitrate", "throughput"):
        return SensorMetadata("data_rate", "bit/s", "measurement", "data_rate", 90)

    if _contains(text, "duration", "runtime", "run time", "uptime"):
        return SensorMetadata("duration", "s", "measurement", "duration", 88)

    if _contains(text, "distance", "range"):
        return SensorMetadata("distance", "m", "measurement", "distance", 85)

    if _contains(text, "wind speed", "speed"):
        return SensorMetadata("speed", "mph", "measurement", "speed", 85)

    if _contains(text, "precipitation", "rain total", "rainfall"):
        return SensorMetadata("precipitation", "in", "total_increasing", "precipitation", 85)

    if device.get("numeric_value") is not None:
        return SensorMetadata(None, None, "measurement", "numeric_sensor", 70)

    return SensorMetadata(None, None, None, "sensor", 60)


def is_strong_sensor_feature(device: dict) -> bool:
    return classify_sensor(device).confidence >= 85
