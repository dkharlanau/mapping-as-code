from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml


class _UniqueKeyLoader(yaml.SafeLoader):
    """Reject explicit duplicates while preserving standard YAML merge overrides."""

    def __init__(self, stream):
        super().__init__(stream)
        self._checked_mappings: set[int] = set()

    def flatten_mapping(self, node):
        if id(node) not in self._checked_mappings:
            self._checked_mappings.add(id(node))
            seen = set()
            for key_node, _ in node.value:
                key = "<<" if key_node.tag == "tag:yaml.org,2002:merge" else self.construct_object(key_node)
                try:
                    duplicate = key in seen
                    seen.add(key)
                except TypeError as exc:
                    raise yaml.constructor.ConstructorError(
                        "while reading a mapping", node.start_mark,
                        "mapping keys must be hashable", key_node.start_mark,
                    ) from exc
                if duplicate:
                    raise yaml.constructor.ConstructorError(
                        "while reading a mapping", node.start_mark,
                        f"duplicate key {key!r}", key_node.start_mark,
                    )
        super().flatten_mapping(node)


def _unique_json_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate key {key!r}")
        result[key] = value
    return result


def load_document(path: str | Path) -> dict[str, Any]:
    """Load a Mapping as Code document from YAML or JSON."""
    source = Path(path)
    text = source.read_text(encoding="utf-8")
    try:
        if source.suffix.lower() == ".json":
            data = json.loads(text, object_pairs_hook=_unique_json_object)
        else:
            data = yaml.load(text, Loader=_UniqueKeyLoader)
    except (yaml.YAMLError, ValueError) as exc:
        raise ValueError(f"{source}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{source}: expected a mapping/object at document root")
    return data
