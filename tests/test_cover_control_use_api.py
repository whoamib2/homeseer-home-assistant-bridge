from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = (ROOT / "custom_components" / "homeseer_bridge" / "api.py").read_text()
COVER = (ROOT / "custom_components" / "homeseer_bridge" / "cover.py").read_text()

def test_control_by_control_use_endpoint_exists():
    assert "async_control_device_by_control_use" in API
    assert '"request": "controldevicebycontroluse"' in API

def test_cover_uses_on_off_control_use():
    assert "control_use=1" in COVER
    assert "control_use=2" in COVER
    assert "async_control_device_by_control_use" in COVER

def test_cover_verifies_actual_homeseer_state():
    assert "async_get_device_status" in API
    assert "actual = await api.async_get_device_status(self.ref)" in COVER
    assert 'self.device["status"] = "Open"' not in COVER
    assert 'self.device["status"] = "Closed"' not in COVER
