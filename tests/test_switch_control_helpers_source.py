from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HELPERS = (ROOT / "custom_components" / "homeseer_bridge" / "helpers.py").read_text()
SWITCH = (ROOT / "custom_components" / "homeseer_bridge" / "switch.py").read_text()

def test_switch_helpers_use_control_use_metadata():
    assert 'control_value_for_use(device, "on")' in HELPERS
    assert 'control_value_for_use(device, "off")' in HELPERS
    assert "def switch_is_on" in HELPERS

def test_switch_entity_no_longer_assumes_positive_value_is_on():
    assert "return value > 0" not in SWITCH
    assert "return switch_is_on(self.device)" in SWITCH
