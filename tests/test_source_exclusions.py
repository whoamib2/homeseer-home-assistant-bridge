from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMP = ROOT / "custom_components" / "homeseer_bridge"

def test_source_filtering_and_registry_cleanup_are_wired():
    init = (COMP / "__init__.py").read_text()
    assert "_async_cleanup_excluded_registry_devices" in init
    assert "async_get_device_by_identifier" in init
    assert "async_remove_device" in init
    assert "excluded_topic_lookup" in init
    assert "excluded_mqtt_drops" in init
    assert "async_remove_config_entry_device" in init

def test_manual_removal_creates_ref_exclusion():
    init = (COMP / "__init__.py").read_text()
    helpers = (COMP / "helpers.py").read_text()
    assert 'token = f"ref:{ref}"' in init
    assert 'term.startswith("ref:")' in helpers

def test_default_exclusions_are_neutral_for_new_installs():
    const = (COMP / "const.py").read_text()
    assert 'DEFAULT_EXCLUDED_TERMS = ""' in const
