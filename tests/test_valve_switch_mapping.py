from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
COMP = ROOT / "custom_components" / "homeseer_bridge"

pkg = types.ModuleType("custom_components.homeseer_bridge")
pkg.__path__ = [str(COMP)]
sys.modules.setdefault("custom_components", types.ModuleType("custom_components"))
sys.modules["custom_components.homeseer_bridge"] = pkg

def load(name):
    spec = spec_from_file_location(
        f"custom_components.homeseer_bridge.{name}",
        COMP / f"{name}.py",
    )
    module = module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module

sensor_metadata = load("sensor_metadata")
capability = load("capability_engine")

def kitchen_valve(value=0, status="On"):
    return {
        "ref": 1055,
        "name": "Kitchen Water Valve",
        "device_type": "Api Feature",
        "interface": "ZWavePlus",
        "relationship": "Feature (Child)",
        "status": status,
        "value": value,
        "numeric_value": float(value),
        "controls": [
            {"Start": 0, "End": 0, "Label": "On", "ControlUse": "On"},
            {"Start": 255, "End": 255, "Label": "Off", "ControlUse": "Off"},
        ],
        "statuses": [
            {"Start": 0, "End": 0, "Status": "On", "StatusUse": "ContactActive"},
            {"Start": 255, "End": 255, "Status": "Off", "StatusUse": "ContactInActive"},
        ],
        "labels_blob": "On Off",
        "control_values": [0, 255],
        "raw_text": "main level kitchen kitchen water valve zwaveplus",
    }

def test_water_valve_is_a_controllable_switch_platform():
    d = kitchen_valve()
    assert capability.capability_platform(d) == "switch"

def test_control_use_exposes_reverse_on_off_values():
    d = kitchen_valve()
    assert capability.control_value_for_use(d, "on") == 0
    assert capability.control_value_for_use(d, "off") == 255

def test_status_metadata_maps_reverse_values_correctly():
    on = capability.resolve_status_text(kitchen_valve(0, "On"), 0)
    off = capability.resolve_status_text(kitchen_valve(255, "Off"), 255)
    assert on.semantic == "active"
    assert off.semantic == "inactive"


def test_valve_name_is_not_apparent_power():
    d = kitchen_valve()
    meta = sensor_metadata.classify_sensor(d)
    assert meta.device_class != "apparent_power"
    assert meta.confidence < 85
