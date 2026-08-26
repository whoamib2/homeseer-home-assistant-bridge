from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = (ROOT / "custom_components" / "homeseer_bridge" / "api.py").read_text()
COVER = (ROOT / "custom_components" / "homeseer_bridge" / "cover.py").read_text()

def test_api_supports_control_by_label():
    assert "async_control_device_by_label" in API
    assert '"request": "controldevicebylabel"' in API
    assert '"label": label' in API

def test_cover_prefers_exact_label_control():
    assert "async_control_device_by_label(self.ref, label)" in COVER
    assert "_cover_label_for_use" in COVER

def test_cover_refreshes_control_metadata_before_command():
    assert "current = await api.async_get_device_status(self.ref)" in COVER

def test_ref_1094_defaults_to_open_closed_labels():
    assert 'return "Open" if expected_open else "Closed"' in COVER
