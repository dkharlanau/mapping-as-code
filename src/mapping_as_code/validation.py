from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


@dataclass(frozen=True)
class Finding:
    code: str
    message: str
    path: str = "$"
    severity: str = "error"

    def __str__(self) -> str:
        return f"{self.severity.upper()} {self.code} {self.path}: {self.message}"


def default_schema_path() -> Path:
    return Path(__file__).resolve().parents[2] / "schemas" / "mapping.schema.json"


def load_schema(path: str | Path | None = None) -> dict[str, Any]:
    schema_path = Path(path) if path else default_schema_path()
    return json.loads(schema_path.read_text(encoding="utf-8"))


def validate_document(document: dict[str, Any], schema: dict[str, Any] | None = None) -> list[Finding]:
    schema = schema or load_schema()
    findings: list[Finding] = []

    validator = Draft202012Validator(schema)
    for error in sorted(validator.iter_errors(document), key=lambda e: list(e.absolute_path)):
        path = "$" + "".join(f"[{part}]" if isinstance(part, int) else f".{part}" for part in error.absolute_path)
        findings.append(Finding("SCHEMA", error.message, path))

    if findings:
        return findings

    fields = document.get("fields", [])
    field_ids: set[str] = set()
    pairs: set[tuple[str, str]] = set()
    target_paths: dict[str, str] = {}
    value_maps = document.get("valueMaps", {})

    for index, field in enumerate(fields):
        field_id = field["id"]
        field_path = f"$.fields[{index}]"
        if field_id in field_ids:
            findings.append(Finding("DUPLICATE_FIELD_ID", f"field id '{field_id}' is repeated", field_path + ".id"))
        field_ids.add(field_id)

        source_path = field.get("source", {}).get("path", "")
        target_path = field["target"]["path"]
        pair = (source_path, target_path)
        if pair in pairs:
            findings.append(Finding("DUPLICATE_MAPPING", f"mapping {source_path!r} -> {target_path!r} is repeated", field_path))
        pairs.add(pair)

        if target_path in target_paths and not field.get("allowMultipleTarget", False):
            findings.append(Finding("TARGET_COLLISION", f"target '{target_path}' is already written by '{target_paths[target_path]}'", field_path + ".target.path"))
        target_paths[target_path] = field_id

        transform = field.get("transform", {"type": "copy"})
        transform_type = transform.get("type", "copy")
        if transform_type == "lookup":
            reference = transform.get("reference")
            if reference not in value_maps:
                findings.append(Finding("MISSING_VALUE_MAP", f"lookup references unknown value map '{reference}'", field_path + ".transform.reference"))

        if transform_type == "constant" and "value" not in transform:
            findings.append(Finding("MISSING_CONSTANT", "constant transform requires 'value'", field_path + ".transform"))

        if transform_type != "constant" and not source_path:
            findings.append(Finding("MISSING_SOURCE", f"transform '{transform_type}' requires source.path", field_path + ".source.path"))

    for name, entries in value_maps.items():
        seen_from: set[str] = set()
        for index, entry in enumerate(entries):
            source_value = str(entry["from"])
            if source_value in seen_from:
                findings.append(Finding("DUPLICATE_VALUE_MAP_KEY", f"value map '{name}' contains duplicate source value '{source_value}'", f"$.valueMaps.{name}[{index}].from"))
            seen_from.add(source_value)

    return findings
