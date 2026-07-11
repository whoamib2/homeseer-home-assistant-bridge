from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
COMP = ROOT / "custom_components" / "homeseer_bridge"

package = types.ModuleType("custom_components.homeseer_bridge")
package.__path__ = [str(COMP)]
sys.modules["custom_components"] = types.ModuleType("custom_components")
sys.modules["custom_components.homeseer_bridge"] = package

spec = spec_from_file_location(
    "custom_components.homeseer_bridge.capability_engine",
    COMP / "capability_engine.py",
)
module = module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

def test_zero_is_inactive_even_when_cached_text_is_active():
    device = {
        "numeric_value": 0.0,
        "status": "On-Open-Motion",
        "statuses": [],
        "value_status_map": {"255": "active"},
    }
    assert module.binary_is_on(device) is False

def test_255_is_active():
    device = {
        "numeric_value": 255.0,
        "status": "Off-Closed-No Motion",
        "statuses": [],
        "value_status_map": {"0": "inactive"},
    }
    assert module.binary_is_on(device) is True

def test_known_nonstandard_mapping_wins():
    device = {
        "numeric_value": 23.0,
        "status": "Window/door is open",
        "statuses": [],
        "value_status_map": {"22": "active", "23": "inactive"},
    }
    assert module.binary_is_on(device) is False
