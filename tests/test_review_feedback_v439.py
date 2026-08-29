import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMP = ROOT / "custom_components" / "homeseer_bridge"

def test_published_topic_map_is_empty_and_private_data_removed():
    text = (COMP / "topic_map.py").read_text()
    assert "Chip23" not in text
    assert "40711405537590095" not in text
    assert "REF_TO_TOPICS: dict[int, list[str]] = {}" in text

def test_name_fallback_only_for_unique_names():
    text = (COMP / "helpers.py").read_text()
    assert "name_refs.setdefault(normalized_name, set()).add(ref)" in text
    assert "candidate_refs.setdefault(normalized, set()).add(ref)" in text
    assert text.count("if len(refs) == 1:") >= 2

def test_hacs_minimum_version_matches_used_apis():
    hacs = json.loads((ROOT / "hacs.json").read_text())
    assert hacs["homeassistant"] == "2026.8.0"

def test_all_five_custom_services_use_admin_registration():
    text = (COMP / "__init__.py").read_text()
    assert "from homeassistant.helpers.service import async_register_admin_service" in text
    assert text.count("async_register_admin_service(") == 5

def test_homeseer_url_credentials_are_redacted():
    text = (COMP / "diagnostics.py").read_text()
    assert "def _redact_url_credentials" in text
    assert 'key_lower == "homeseer_url"' in text
    assert "parsed.username" in text
    assert "parsed.password" in text

def test_light_and_fan_guard_non_numeric_capi_values():
    light = (COMP / "light.py").read_text()
    fan = (COMP / "fan.py").read_text()
    assert "except (TypeError, ValueError):" in light
    assert "except (TypeError, ValueError):" in fan
    assert 'self.device["value"] = hs_value' in light
    assert 'self.device["value"] = value' in fan


def test_optional_dashboard_is_admin_only():
    text = (COMP / "dashboard.py").read_text()
    assert "CONF_REQUIRE_ADMIN: True" in text


def test_bundled_docs_and_tools_do_not_ship_private_installation_defaults():
    paths = [
        ROOT / "docs" / "INSTALL.md",
        ROOT / "tools" / "mcsmqtt_bulk_enable.py",
        ROOT / "tools" / "enable_ref_1359_example.bat",
        ROOT / "tools" / "README_MCSMQTT_BULK_ENABLE.md",
    ]
    combined = "\n".join(path.read_text() for path in paths)
    for private_value in (
        "192.168.0.193",
        "Homeseer/Chip23/mcsMQTT",
        "192.168.0.5",
        "august,yolink,shelly",
    ):
        assert private_value not in combined
