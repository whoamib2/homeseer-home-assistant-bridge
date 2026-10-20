import ast
import asyncio
import importlib
import logging
from pathlib import Path
import sys
import types
from unittest.mock import Mock


COMP = Path(__file__).resolve().parents[1] / "custom_components" / "homeseer_bridge"


def _removal_context(options=None):
    # Load the real callback and its constant imports without starting Home Assistant.
    package_name = "_homeseer_device_removal_test"
    package = types.ModuleType(package_name)
    package.__path__ = [str(COMP)]
    sys.modules[package_name] = package
    helpers = importlib.import_module(f"{package_name}.helpers")
    source = ast.parse((COMP / "__init__.py").read_text())
    nodes = [
        node for node in source.body
        if (
            isinstance(node, ast.ImportFrom)
            and node.module in {"__future__", "const"}
        ) or (
            isinstance(node, ast.AsyncFunctionDef)
            and node.name == "async_remove_config_entry_device"
        )
    ]
    namespace = {
        "__package__": package_name,
        "_LOGGER": logging.getLogger(__name__),
        "excluded_terms": helpers.excluded_terms,
        "build_topic_lookup": helpers.build_topic_lookup,
    }
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(COMP / "__init__.py"), "exec"), namespace)
    entry = types.SimpleNamespace(
        entry_id="test-entry",
        data={"excluded_terms": "weather", "mqtt_prefix": "test/home"},
        options=dict(options or {"keep_option": True}),
    )
    state = {1234: {"name": "Removed device"}, 5678: {"name": "Kept device"}}
    runtime = {"state": state, "topic_lookup": helpers.build_topic_lookup(state, entry)}
    update = Mock(side_effect=lambda entry, *, options: setattr(entry, "options", options))
    hass = types.SimpleNamespace(
        config_entries=types.SimpleNamespace(async_update_entry=update),
        data={"homeseer_bridge": {entry.entry_id: runtime}},
    )
    device = types.SimpleNamespace(identifiers={("homeseer_bridge", "1234")})
    return namespace["async_remove_config_entry_device"], hass, entry, device


def test_first_removal_persists_exclusion_and_cleans_runtime_state():
    remove, hass, entry, device = _removal_context()
    assert asyncio.run(remove(hass, entry, device)) is True
    assert entry.options == {"keep_option": True, "excluded_terms": "weather,ref:1234"}
    hass.config_entries.async_update_entry.assert_called_once()
    runtime = hass.data["homeseer_bridge"][entry.entry_id]
    assert set(runtime["state"]) == {5678}
    assert set(runtime["topic_lookup"].values()) == {5678}


def test_removal_preserves_option_exclusions_ahead_of_data_defaults():
    remove, hass, entry, device = _removal_context({"excluded_terms": "debug", "keep_option": True})
    assert asyncio.run(remove(hass, entry, device)) is True
    assert entry.options == {"excluded_terms": "debug,ref:1234", "keep_option": True}


def test_repeated_removal_does_not_duplicate_exclusions():
    remove, hass, entry, device = _removal_context()
    assert asyncio.run(remove(hass, entry, device)) is True
    assert asyncio.run(remove(hass, entry, device)) is True
    assert entry.options["excluded_terms"] == "weather,ref:1234"
    hass.config_entries.async_update_entry.assert_called_once()


def test_bridge_or_foreign_device_is_not_removed():
    remove, hass, entry, _ = _removal_context()
    for identifiers in [{("homeseer_bridge", "bridge")}, {("other_integration", "1234")}]:
        assert asyncio.run(remove(hass, entry, types.SimpleNamespace(identifiers=identifiers))) is False
    hass.config_entries.async_update_entry.assert_not_called()
    assert set(hass.data["homeseer_bridge"][entry.entry_id]["state"]) == {1234, 5678}
