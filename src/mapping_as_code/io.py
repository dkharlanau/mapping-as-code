from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml


def load_document(path: str | Path) -> dict[str, Any]:
    """Load a Mapping as Code document from YAML or JSON."""
    source = Path(path)
    text = source.read_text(encoding="utf-8")
    if source.suffix.lower() == ".json":
        data = json.loads(text)
    else:
        data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError(f"{source}: expected a mapping/object at document root")
    return data
