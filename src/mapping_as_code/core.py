from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


_ALLOWED_TRANSFORMS = {
    "copy",
    "lookup",
    "constant",
    "expression",
    "concat",
    "split",
    "date",
    "number",
    "boolean",
}


@dataclass(frozen=True)
class Diagnostic:
    code: str
    message: str
    path: str
    severity: str = "error"

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


def _is_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _endpoint(endpoint: Any, role: str, index: int, diagnostics: list[Diagnostic]) -> dict[str, Any]:
    path = f"mapping.fields[{index}].{role}"
    if not isinstance(endpoint, dict):
        diagnostics.append(Diagnostic("endpoint.invalid", f"{role} must be an object", path))
        return {}
    field = endpoint.get("field")
    if not _is_nonempty_string(field):
        diagnostics.append(Diagnostic("endpoint.field.missing", f"{role}.field is required", f"{path}.field"))
    return endpoint


def validate_document(document: dict[str, Any]) -> list[Diagnostic]:
    """Validate structural and semantic mapping invariants."""
    diagnostics: list[Diagnostic] = []

    if not _is_nonempty_string(document.get("schema_version")):
        diagnostics.append(Diagnostic("schema-version.missing", "schema_version is required", "schema_version"))

    mapping = document.get("mapping")
    if not isinstance(mapping, dict):
        diagnostics.append(Diagnostic("mapping.missing", "mapping object is required", "mapping"))
        return diagnostics

    if not _is_nonempty_string(mapping.get("id")):
        diagnostics.append(Diagnostic("mapping.id.missing", "mapping.id is required", "mapping.id"))

    for role in ("source", "target"):
        endpoint = mapping.get(role)
        if not isinstance(endpoint, dict):
            diagnostics.append(Diagnostic("mapping.endpoint.missing", f"mapping.{role} is required", f"mapping.{role}"))
            continue
        for key in ("system", "object"):
            if not _is_nonempty_string(endpoint.get(key)):
                diagnostics.append(
                    Diagnostic("mapping.endpoint.invalid", f"mapping.{role}.{key} is required", f"mapping.{role}.{key}")
                )

    fields = mapping.get("fields")
    if not isinstance(fields, list) or not fields:
        diagnostics.append(Diagnostic("fields.missing", "mapping.fields must contain at least one field mapping", "mapping.fields"))
        return diagnostics

    value_maps = document.get("value_maps", {})
    if value_maps is None:
        value_maps = {}
    if not isinstance(value_maps, dict):
        diagnostics.append(Diagnostic("value-maps.invalid", "value_maps must be an object", "value_maps"))
        value_maps = {}

    seen_ids: dict[str, int] = {}
    target_owners: dict[str, int] = {}
    mapped_targets: set[str] = set()
    mapped_sources: set[str] = set()

    for index, field_map in enumerate(fields):
        base = f"mapping.fields[{index}]"
        if not isinstance(field_map, dict):
            diagnostics.append(Diagnostic("field.invalid", "field mapping must be an object", base))
            continue

        field_id = field_map.get("id")
        if not _is_nonempty_string(field_id):
            diagnostics.append(Diagnostic("field.id.missing", "field mapping id is required", f"{base}.id"))
        else:
            if field_id in seen_ids:
                diagnostics.append(
                    Diagnostic(
                        "field.id.duplicate",
                        f"duplicate field mapping id '{field_id}' (first used at index {seen_ids[field_id]})",
                        f"{base}.id",
                    )
                )
            else:
                seen_ids[field_id] = index

        transform = field_map.get("transform") or {"type": "copy"}
        if not isinstance(transform, dict):
            diagnostics.append(Diagnostic("transform.invalid", "transform must be an object", f"{base}.transform"))
            transform = {}
        transform_type = transform.get("type", "copy")
        if transform_type not in _ALLOWED_TRANSFORMS:
            diagnostics.append(
                Diagnostic(
                    "transform.unsupported",
                    f"unsupported transform type '{transform_type}'",
                    f"{base}.transform.type",
                )
            )

        target = _endpoint(field_map.get("target"), "target", index, diagnostics)
        target_field = target.get("field")
        if _is_nonempty_string(target_field):
            mapped_targets.add(target_field)
            if target_field in target_owners and not field_map.get("allow_multiple_sources", False):
                diagnostics.append(
                    Diagnostic(
                        "target.duplicate",
                        f"target field '{target_field}' is mapped more than once",
                        f"{base}.target.field",
                    )
                )
            else:
                target_owners[target_field] = index

        if transform_type != "constant":
            source = _endpoint(field_map.get("source"), "source", index, diagnostics)
            source_field = source.get("field")
            if _is_nonempty_string(source_field):
                mapped_sources.add(source_field)

        if transform_type == "lookup":
            reference = transform.get("reference")
            if not _is_nonempty_string(reference):
                diagnostics.append(
                    Diagnostic("lookup.reference.missing", "lookup transform requires reference", f"{base}.transform.reference")
                )
            elif reference not in value_maps:
                diagnostics.append(
                    Diagnostic(
                        "lookup.reference.unknown",
                        f"lookup references undefined value map '{reference}'",
                        f"{base}.transform.reference",
                    )
                )

        if transform_type == "constant" and "value" not in transform:
            diagnostics.append(
                Diagnostic("constant.value.missing", "constant transform requires value", f"{base}.transform.value")
            )

        rules = field_map.get("rules", {})
        if rules is not None and not isinstance(rules, dict):
            diagnostics.append(Diagnostic("rules.invalid", "rules must be an object", f"{base}.rules"))

    required_targets = mapping.get("target", {}).get("required_fields", []) if isinstance(mapping.get("target"), dict) else []
    if required_targets is None:
        required_targets = []
    if not isinstance(required_targets, list):
        diagnostics.append(
            Diagnostic("target.required-fields.invalid", "target.required_fields must be a list", "mapping.target.required_fields")
        )
    else:
        for required in required_targets:
            if _is_nonempty_string(required) and required not in mapped_targets:
                diagnostics.append(
                    Diagnostic(
                        "target.required.unmapped",
                        f"required target field '{required}' has no mapping",
                        "mapping.target.required_fields",
                    )
                )

    required_sources = mapping.get("source", {}).get("required_fields", []) if isinstance(mapping.get("source"), dict) else []
    if required_sources is None:
        required_sources = []
    if not isinstance(required_sources, list):
        diagnostics.append(
            Diagnostic("source.required-fields.invalid", "source.required_fields must be a list", "mapping.source.required_fields")
        )
    else:
        for required in required_sources:
            if _is_nonempty_string(required) and required not in mapped_sources:
                diagnostics.append(
                    Diagnostic(
                        "source.required.unused",
                        f"required source field '{required}' is not used",
                        "mapping.source.required_fields",
                        severity="warning",
                    )
                )

    return diagnostics


def mapping_summary(document: dict[str, Any]) -> dict[str, Any]:
    mapping = document.get("mapping") if isinstance(document.get("mapping"), dict) else {}
    fields = mapping.get("fields") if isinstance(mapping.get("fields"), list) else []
    required = mapping.get("target", {}).get("required_fields", []) if isinstance(mapping.get("target"), dict) else []
    required = required if isinstance(required, list) else []
    mapped = {
        item.get("target", {}).get("field")
        for item in fields
        if isinstance(item, dict) and isinstance(item.get("target"), dict)
    }
    mapped.discard(None)
    covered = sum(1 for field in required if field in mapped)
    return {
        "mapping_id": mapping.get("id"),
        "field_mappings": len(fields),
        "required_targets": len(required),
        "covered_required_targets": covered,
        "coverage": 1.0 if not required else covered / len(required),
    }


def _field_index(document: dict[str, Any]) -> dict[str, dict[str, Any]]:
    mapping = document.get("mapping") if isinstance(document.get("mapping"), dict) else {}
    fields = mapping.get("fields") if isinstance(mapping.get("fields"), list) else []
    result: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(fields):
        if not isinstance(item, dict):
            continue
        key = item.get("id")
        if not _is_nonempty_string(key):
            target = item.get("target") if isinstance(item.get("target"), dict) else {}
            key = f"@target:{target.get('field', index)}"
        result[str(key)] = item
    return result


def diff_documents(old: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
    """Return a stable, machine-readable field mapping diff."""
    old_index = _field_index(old)
    new_index = _field_index(new)
    old_keys = set(old_index)
    new_keys = set(new_index)

    changed: list[dict[str, Any]] = []
    for key in sorted(old_keys & new_keys):
        before = old_index[key]
        after = new_index[key]
        changes: dict[str, dict[str, Any]] = {}
        for section in ("source", "target", "transform", "rules", "business"):
            if before.get(section) != after.get(section):
                changes[section] = {"before": before.get(section), "after": after.get(section)}
        if changes:
            changed.append({"id": key, "changes": changes})

    return {
        "old_mapping_id": (old.get("mapping") or {}).get("id") if isinstance(old.get("mapping"), dict) else None,
        "new_mapping_id": (new.get("mapping") or {}).get("id") if isinstance(new.get("mapping"), dict) else None,
        "added": sorted(new_keys - old_keys),
        "removed": sorted(old_keys - new_keys),
        "changed": changed,
        "has_changes": bool((new_keys - old_keys) or (old_keys - new_keys) or changed),
    }


def lineage_graph(document: dict[str, Any]) -> dict[str, Any]:
    """Build a portable field-level lineage graph."""
    mapping = document.get("mapping") if isinstance(document.get("mapping"), dict) else {}
    source = mapping.get("source") if isinstance(mapping.get("source"), dict) else {}
    target = mapping.get("target") if isinstance(mapping.get("target"), dict) else {}
    fields = mapping.get("fields") if isinstance(mapping.get("fields"), list) else []

    source_prefix = f"{source.get('system', 'source')}.{source.get('object', 'object')}"
    target_prefix = f"{target.get('system', 'target')}.{target.get('object', 'object')}"
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []

    for index, item in enumerate(fields):
        if not isinstance(item, dict):
            continue
        transform = item.get("transform") if isinstance(item.get("transform"), dict) else {"type": "copy"}
        transform_type = transform.get("type", "copy")
        target_ep = item.get("target") if isinstance(item.get("target"), dict) else {}
        target_field = target_ep.get("field")
        if not _is_nonempty_string(target_field):
            continue
        target_id = f"{target_prefix}.{target_field}"
        nodes[target_id] = {"id": target_id, "kind": "target_field", "field": target_field}

        if transform_type == "constant":
            source_id = f"constant:{item.get('id', index)}"
            nodes[source_id] = {"id": source_id, "kind": "constant", "value": transform.get("value")}
        else:
            source_ep = item.get("source") if isinstance(item.get("source"), dict) else {}
            source_field = source_ep.get("field")
            if not _is_nonempty_string(source_field):
                continue
            source_id = f"{source_prefix}.{source_field}"
            nodes[source_id] = {"id": source_id, "kind": "source_field", "field": source_field}

        edges.append(
            {
                "id": item.get("id", f"field-{index}"),
                "from": source_id,
                "to": target_id,
                "transform": transform_type,
                "reference": transform.get("reference"),
            }
        )

    return {"nodes": sorted(nodes.values(), key=lambda item: item["id"]), "edges": edges}


def lineage_mermaid(document: dict[str, Any]) -> str:
    graph = lineage_graph(document)
    node_aliases = {node["id"]: f"n{index}" for index, node in enumerate(graph["nodes"])}
    lines = ["flowchart LR"]
    for node in graph["nodes"]:
        label = str(node["id"]).replace('"', "'")
        lines.append(f'  {node_aliases[node["id"]]}["{label}"]')
    for edge in graph["edges"]:
        label = str(edge.get("transform", "copy")).replace('"', "'")
        lines.append(f'  {node_aliases[edge["from"]]} -->|{label}| {node_aliases[edge["to"]]}')
    return "\n".join(lines) + "\n"
