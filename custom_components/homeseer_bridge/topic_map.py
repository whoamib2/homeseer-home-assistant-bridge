"""Optional exact MQTT topic mappings.

The published integration intentionally ships with no installation-specific
HomeSeer refs or MQTT topics. Runtime lookup is generated from each user's
HomeSeer metadata.
"""

REF_TO_TOPICS: dict[int, list[str]] = {}
