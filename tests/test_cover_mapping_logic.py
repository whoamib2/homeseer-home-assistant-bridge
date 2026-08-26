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

capability = load("capability_engine")


def big_garage():
    return {
        "ref": 1094,
        "name": "Big Garage Door State",
        "location": "Garage",
        "location2": "Main Level",
        "status": "Closed",
        "numeric_value": 0.0,
        "controls": [
            {"Start": 0, "End": 0, "Label": "Closed", "ControlUse": "Off"},
            {"Start": 100, "End": 100, "Label": "Open", "ControlUse": "On"},
        ],
        "statuses": [
            {"Start": 0, "End": 0, "Status": "Closed", "StatusUse": "NotSpecified"},
            {"Start": 100, "End": 100, "Status": "Open", "StatusUse": "NotSpecified"},
        ],
    }


def test_ref_1094_control_values():
    d = big_garage()
    assert capability.control_value_for_use(d, "on") == 100
    assert capability.control_value_for_use(d, "off") == 0


def test_ref_1094_status_resolution():
    d = big_garage()
    assert capability.resolve_status_text(d, 0).text == "Closed"
    assert capability.resolve_status_text(d, 100).text == "Open"
