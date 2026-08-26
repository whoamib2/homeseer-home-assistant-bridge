from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
COMP = ROOT / "custom_components" / "homeseer_bridge"


def test_dashboard_does_not_write_lovelace_store_directly():
    dashboard = (COMP / "dashboard.py").read_text()
    assert "homeassistant.helpers.storage import Store" not in dashboard
    assert "Store(" not in dashboard
    assert "DashboardsCollection" in dashboard
    assert "LovelaceStorage" in dashboard


def test_dashboard_is_not_created_during_setup():
    init = (COMP / "__init__.py").read_text()
    assert "async_create_task(async_ensure_dashboard" not in init
    assert "handle_create_dashboard" in init


def test_virtual_poll_default_is_at_least_30_seconds():
    const = (COMP / "const.py").read_text()
    match = re.search(r"DEFAULT_VIRTUAL_POLL_INTERVAL_SECONDS\s*=\s*(\d+)", const)
    assert match is not None
    assert int(match.group(1)) >= 30


def test_new_install_defaults_are_not_personal_installation_values():
    const = (COMP / "const.py").read_text()
    assert 'DEFAULT_HS_URL = ""' in const
    assert 'DEFAULT_MQTT_PREFIX = ""' in const
    assert 'DEFAULT_EXCLUDED_TERMS = ""' in const
    assert 'DEFAULT_ACTIVITY_EXCLUDED_TERMS = ""' in const
    assert "192.168.0.193" not in const
    assert "Chip23" not in const
    assert "august,yolink" not in const
    assert "utility,jon00" not in const


def test_readme_starts_with_project_description_not_changelog():
    readme = (ROOT / "README.md").read_text()
    assert readme.find("## Features") > 0
    assert "## v4.3.4" not in readme[:4000]
