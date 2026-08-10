from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys, types

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

metadata = load("sensor_metadata")
capability = load("capability_engine")

def test_lock_battery_child_is_sensor_not_lock():
    d = {
        "ref": 3174,
        "name": "1300 Front Door Lock - Battery",
        "device_type": "Api Feature",
        "interface": "ZWavePlus",
        "relationship": "Feature (Child)",
        "status": "99%",
        "value": 99,
        "numeric_value": 99.0,
        "labels_blob": "",
        "controls": [],
        "statuses": [],
        "raw_text": "front door lock assa abloy secured unsecured doorlock battery",
    }
    m = metadata.classify_sensor(d)
    assert capability.capability_platform(d) == "sensor"
    assert (m.device_class, m.unit, m.state_class) == ("battery", "%", "measurement")

def test_real_door_lock_child_stays_lock():
    d = {
        "ref": 3176,
        "name": "1300 Front Door Lock - Door Lock",
        "device_type": "Api Feature",
        "interface": "ZWavePlus",
        "relationship": "Feature (Child)",
        "status": "Unsecured",
        "numeric_value": 0.0,
        "labels_blob": "unlock doorunlock lock doorlock",
        "controls": [],
        "statuses": [],
        "raw_text": "front door lock secured unsecured doorlock doorunlock",
    }
    assert capability.capability_platform(d) == "lock"
