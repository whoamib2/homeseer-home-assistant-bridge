import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "custom_components" / "homeseer_bridge" / "manifest.json"

def test_mqtt_dependency_and_optional_lovelace_after_dependency():
    manifest = json.loads(MANIFEST.read_text())
    assert manifest["dependencies"] == ["mqtt"]
    assert manifest["after_dependencies"] == ["lovelace"]

def test_release_remains_current():
    manifest = json.loads(MANIFEST.read_text())
    assert manifest["version"] == "4.3.9"
