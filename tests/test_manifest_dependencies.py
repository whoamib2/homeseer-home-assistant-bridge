import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "custom_components" / "homeseer_bridge" / "manifest.json"

def test_lovelace_and_mqtt_declared_as_dependencies():
    manifest = json.loads(MANIFEST.read_text())
    assert "lovelace" in manifest["dependencies"]
    assert "mqtt" in manifest["dependencies"]

def test_release_remains_current():
    manifest = json.loads(MANIFEST.read_text())
    assert manifest["version"] == "4.3.7"
