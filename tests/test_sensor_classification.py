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
    spec = spec_from_file_location(f"custom_components.homeseer_bridge.{name}", COMP / f"{name}.py")
    module = module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module

metadata = load("sensor_metadata")
capability = load("capability_engine")

def test_battery_child_stays_sensor_despite_parent_door_metadata():
    d = {"name":"Front Door - Battery","device_type":"Api Feature","interface":"ZWavePlus",
         "status":"100%","numeric_value":100.0,"raw_text":"parent door/window contact motion",
         "statuses":[],"controls":[]}
    m = metadata.classify_sensor(d)
    assert capability.capability_platform(d) == "sensor"
    assert (m.device_class, m.unit, m.state_class) == ("battery","%","measurement")

def test_voltage_sensor():
    m = metadata.classify_sensor({"name":"Electric Consumption [V]","numeric_value":121.2})
    assert (m.device_class, m.unit) == ("voltage","V")

def test_energy_total_increasing():
    m = metadata.classify_sensor({"name":"Electric Consumption [kWh]","numeric_value":1432.1})
    assert (m.device_class, m.unit, m.state_class) == ("energy","kWh","total_increasing")

def test_door_sensor_remains_binary():
    d = {"name":"Front Door Sensor","device_type":"Binary Sensor","status":"On-Open-Motion",
         "numeric_value":255.0,"statuses":[],"controls":[]}
    assert capability.capability_platform(d) == "binary_sensor"
