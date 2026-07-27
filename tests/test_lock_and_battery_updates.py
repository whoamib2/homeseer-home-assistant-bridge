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

def lock_device(value, status="", last=None):
    return {
        "name": "Front Door Lock - Door Lock",
        "device_type": "Api Feature",
        "interface": "ZWavePlus",
        "numeric_value": float(value),
        "value": value,
        "status": status,
        "last_known_lock_state": last,
        "statuses": [],
        "controls": [],
        "labels_blob": "unlock doorunlock lock doorlock",
    }

def test_unsecured_text_is_unlocked():
    assert capability.lock_state(lock_device(0, "Unsecured")) == "unlocked"

def test_secured_text_is_locked():
    assert capability.lock_state(lock_device(255, "Secured")) == "locked"

def test_unsecured_variant_values_are_unlocked():
    for value in (0, 1, 16, 17, 32, 33):
        assert capability.lock_state(lock_device(value)) == "unlocked"

def test_254_preserves_last_known_lock_state():
    assert capability.lock_state(lock_device(254, "Unknown", "unlocked")) == "unlocked"
    assert capability.lock_state(lock_device(254, "Unknown", "locked")) == "locked"

def test_battery_remains_numeric_sensor():
    device = {
        "name": "Front Door Lock - Battery",
        "device_type": "Api Feature",
        "interface": "ZWavePlus",
        "numeric_value": 99.0,
        "value": "99",
        "status": "99%",
    }
    metadata = sensor_metadata.classify_sensor(device)
    assert metadata.device_class == "battery"
    assert metadata.unit == "%"
    assert metadata.state_class == "measurement"
    assert capability.capability_platform(device) == "sensor"
