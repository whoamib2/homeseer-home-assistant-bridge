from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
text = (ROOT / "custom_components" / "homeseer_bridge" / "helpers.py").read_text()

def test_all_platform_helpers_delegate_to_capability_classifier():
    for expected in (
        'return capability_platform(device) == "lock"',
        'return capability_platform(device) == "cover"',
        'return capability_platform(device) == "binary_sensor"',
        'return capability_platform(device) == "fan"',
        'return capability_platform(device) == "light"',
        'return capability_platform(device) == "switch"',
        'return capability_platform(device) == "sensor"',
    ):
        assert expected in text
