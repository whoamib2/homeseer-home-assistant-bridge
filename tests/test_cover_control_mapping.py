from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COVER = (ROOT / "custom_components" / "homeseer_bridge" / "cover.py").read_text()


def test_cover_commands_are_not_hard_coded():
    assert 'async_control_device_by_value(self.ref, 255)' not in COVER
    assert 'async_control_device_by_value(self.ref, 0)' not in COVER
    assert 'value = cover_open_value(self.device)' in COVER
    assert 'value = cover_close_value(self.device)' in COVER


def test_big_garage_virtual_switch_mapping_is_supported():
    # Ref 1094 in HomeSeer:
    # 0 = Closed, ControlUse=Off
    # 100 = Open, ControlUse=On
    assert 'control_value_for_use(device, "on", "open")' in COVER
    assert 'control_value_for_use(device, "off", "close", "closed")' in COVER
