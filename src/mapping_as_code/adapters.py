from __future__ import annotations

import re
from pathlib import Path
from typing import Any


def _mapping(document: dict[str, Any]) -> dict[str, Any]:
    mapping = document.get("mapping")
    if not isinstance(mapping, dict):
        raise ValueError("mapping object is required")
    return mapping


def _slug(value: Any, *, lower: bool = False) -> str:
    text = str(value or "").strip()
    text = re.sub(r"[^A-Za-z0-9._-]+", "-", text).strip("-")
    if lower:
        text = text.lower()
    return text or "mapping"


def _graph_id(*parts: Any) -> str:
    return ":".join(_slug(part) for part in parts if part is not None)


def _visual_id(*parts: Any) -> str:
    return "-".join(_slug(part) for part in parts if part is not None)


def _criticality(field: dict[str, Any]) -> str | None:
    business = field.get("business") if isinstance(field.get("business"), dict) else {}
    value = str(business.get("criticality", "")).lower()
    return value if value in {"low", "medium", "high", "critical"} else None


def _dedupe_nodes(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for node in nodes:
        result[node["id"]] = node
    return list(result.values())


def to_transformation_graph(document: dict[str, Any]) -> dict[str, Any]:
    mapping = _mapping(document)
    source = mapping.get("source") if isinstance(mapping.get("source"), dict) else {}
    target = mapping.get("target") if isinstance(mapping.get("target"), dict) else {}
    fields = mapping.get("fields") if isinstance(mapping.get("fields"), list) else []
    mapping_id = str(mapping.get("id") or "mapping")
    title = str(mapping.get("title") or mapping_id)

    source_system_id = _graph_id("system", source.get("system", "source"))
    target_system_id = _graph_id("system", target.get("system", "target"))
    source_object_id = _graph_id("object", source.get("system", "source"), source.get("object", "object"))
    target_object_id = _graph_id("object", target.get("system", "target"), target.get("object", "object"))
    mapping_set_id = _graph_id("mapping", mapping_id)

    nodes: list[dict[str, Any]] = [
        {"id": source_system_id, "type": "system", "title": str(source.get("system", "source"))},
        {"id": target_system_id, "type": "system", "title": str(target.get("system", "target"))},
        {"id": source_object_id, "type": "business_object", "title": str(source.get("object", "source object"))},
        {"id": target_object_id, "type": "business_object", "title": str(target.get("object", "target object"))},
        {
            "id": mapping_set_id,
            "type": "mapping",
            "title": title,
            "description": str(mapping.get("description") or "Mapping as Code projection"),
            "attributes": {"mapping_id": mapping_id, "schema_version": document.get("schema_version")},
        },
    ]
    edges: list[dict[str, Any]] = [
        {"from": source_system_id, "to": source_object_id, "type": "contains"},
        {"from": target_system_id, "to": target_object_id, "type": "contains"},
    ]

    for index, field in enumerate(fields):
        if not isinstance(field, dict):
            continue
        field_id = str(field.get("id") or f"field-{index}")
        map_node_id = _graph_id("mapping", mapping_id, field_id)
        transform = field.get("transform") if isinstance(field.get("transform"), dict) else {"type": "copy"}
        business = field.get("business") if isinstance(field.get("business"), dict) else {}
        nodes.append(
            {
                "id": map_node_id,
                "type": "mapping",
                "title": field_id,
                "attributes": {
                    "transform": transform,
                    "rules": field.get("rules") if isinstance(field.get("rules"), dict) else {},
                    "business": business,
                },
            }
        )
        edges.append({"from": mapping_set_id, "to": map_node_id, "type": "contains_mapping"})

        target_ep = field.get("target") if isinstance(field.get("target"), dict) else {}
        target_field = target_ep.get("field")
        if target_field:
            target_field_id = _graph_id("field", target.get("system", "target"), target.get("object", "object"), target_field)
            nodes.append({"id": target_field_id, "type": "field", "title": str(target_field)})
            edges.append({"from": target_object_id, "to": target_field_id, "type": "contains"})
            edges.append(
                {
                    "from": map_node_id,
                    "to": target_field_id,
                    "type": "maps_to",
                    "label": str(transform.get("type", "copy")),
                }
            )

        source_ep = field.get("source") if isinstance(field.get("source"), dict) else {}
        source_field = source_ep.get("field")
        if source_field:
            source_field_id = _graph_id("field", source.get("system", "source"), source.get("object", "object"), source_field)
            nodes.append({"id": source_field_id, "type": "field", "title": str(source_field)})
            edges.append({"from": source_object_id, "to": source_field_id, "type": "contains"})
            edges.append({"from": source_field_id, "to": map_node_id, "type": "input_to"})
        elif transform.get("type") == "constant":
            edges.append(
                {
                    "from": mapping_set_id,
                    "to": map_node_id,
                    "type": "defines",
                    "label": f"constant={transform.get('value')}",
                }
            )

    return {
        "version": "0.1",
        "project": {
            "id": _slug(mapping_id, lower=True),
            "name": title,
            "description": str(mapping.get("description") or "Generated from Mapping as Code"),
        },
        "nodes": _dedupe_nodes(nodes),
        "edges": edges,
    }


def to_enterprise_change_graph(document: dict[str, Any]) -> dict[str, Any]:
    tg = to_transformation_graph(document)
    nodes = []
    for node in tg["nodes"]:
        attributes = node.get("attributes") if isinstance(node.get("attributes"), dict) else {}
        criticality = None
        business = attributes.get("business") if isinstance(attributes.get("business"), dict) else {}
        candidate = str(business.get("criticality", "")).lower()
        if candidate in {"low", "medium", "high", "critical"}:
            criticality = candidate
        item: dict[str, Any] = {
            "id": node["id"],
            "type": node["type"],
            "name": node.get("title", node["id"]),
            "metadata": attributes,
            "provenance": "mapping-as-code",
        }
        if criticality:
            item["criticality"] = criticality
        nodes.append(item)

    edges = [
        {
            "source": edge["from"],
            "target": edge["to"],
            "relation": edge["type"],
            "propagation": "forward",
            "metadata": {"label": edge.get("label")} if edge.get("label") else {},
            "provenance": "mapping-as-code",
        }
        for edge in tg["edges"]
    ]
    return {
        "version": 1,
        "metadata": {
            "source": "mapping-as-code",
            "mapping_id": _mapping(document).get("id"),
            "schema_version": document.get("schema_version"),
        },
        "nodes": nodes,
        "edges": edges,
    }


def to_visual_workbench(document: dict[str, Any]) -> dict[str, Any]:
    mapping = _mapping(document)
    source = mapping.get("source") if isinstance(mapping.get("source"), dict) else {}
    target = mapping.get("target") if isinstance(mapping.get("target"), dict) else {}
    fields = mapping.get("fields") if isinstance(mapping.get("fields"), list) else []
    title = str(mapping.get("title") or mapping.get("id") or "Mapping")

    groups = [
        {"id": "source", "label": f'{source.get("system", "Source")} · {source.get("object", "Object")}', "kind": "lane", "order": 1},
        {"id": "mapping", "label": "Mapping rules", "kind": "lane", "order": 2},
        {"id": "target", "label": f'{target.get("system", "Target")} · {target.get("object", "Object")}', "kind": "lane", "order": 3},
    ]
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []

    for index, field in enumerate(fields):
        if not isinstance(field, dict):
            continue
        field_id = str(field.get("id") or f"field-{index}")
        transform = field.get("transform") if isinstance(field.get("transform"), dict) else {"type": "copy"}
        map_id = _visual_id("map", field_id)
        business = field.get("business") if isinstance(field.get("business"), dict) else {}
        criticality = _criticality(field)
        status = "danger" if criticality == "critical" else "warning" if criticality == "high" else "neutral"
        map_node: dict[str, Any] = {
            "id": map_id,
            "label": field_id,
            "type": "step",
            "subtitle": str(transform.get("type", "copy")),
            "group": "mapping",
            "status": status,
            "tags": [value for value in [criticality, str(business.get("owner")) if business.get("owner") else None] if value],
        }
        if business.get("rationale"):
            map_node["description"] = str(business["rationale"])
        nodes.append(map_node)

        source_ep = field.get("source") if isinstance(field.get("source"), dict) else {}
        source_field = source_ep.get("field")
        if source_field:
            src_id = _visual_id("src", source_field)
            nodes.append({"id": src_id, "label": str(source_field), "type": "data", "group": "source"})
        else:
            src_id = _visual_id("const", field_id)
            nodes.append(
                {
                    "id": src_id,
                    "label": f'Constant: {transform.get("value")}',
                    "type": "data",
                    "group": "source",
                    "status": "muted",
                }
            )
        edges.append({"from": src_id, "to": map_id, "type": "data"})

        target_ep = field.get("target") if isinstance(field.get("target"), dict) else {}
        target_field = target_ep.get("field")
        if target_field:
            tgt_id = _visual_id("tgt", target_field)
            nodes.append({"id": tgt_id, "label": str(target_field), "type": "data", "group": "target"})
            edges.append(
                {
                    "from": map_id,
                    "to": tgt_id,
                    "type": "data",
                    "label": str(transform.get("type", "copy")),
                    "status": status,
                }
            )

    return {
        "visual": {
            "version": 1,
            "title": title,
            "description": str(mapping.get("description") or "Field mapping lineage generated from Mapping as Code"),
            "kind": "data-flow",
            "direction": "right",
            "theme": "paper",
            "density": "airy",
            "groups": groups,
            "nodes": _dedupe_nodes(nodes),
            "edges": edges,
            "views": [
                {
                    "id": "data",
                    "title": "Field mapping",
                    "focus": "data",
                    "kind": "data-flow",
                    "direction": "right",
                    "includeNodeTypes": ["data", "step"],
                    "includeEdgeTypes": ["data"],
                }
            ],
        }
    }


def _format_for_file(path: str) -> str | None:
    suffix = Path(path).suffix.lower().lstrip(".")
    return suffix if suffix in {"csv", "xlsx", "xlsm", "parquet"} else None


def _key_value(value: str | list[str]) -> str | list[str]:
    if isinstance(value, list):
        return value
    values = [part.strip() for part in str(value).split(",") if part.strip()]
    if not values:
        raise ValueError("reconciliation keys must not be empty")
    return values if len(values) > 1 else values[0]


def to_reconciliation(
    document: dict[str, Any],
    *,
    source_file: str,
    target_file: str,
    source_key: str | list[str],
    target_key: str | list[str],
) -> dict[str, Any]:
    mapping = _mapping(document)
    source = mapping.get("source") if isinstance(mapping.get("source"), dict) else {}
    target = mapping.get("target") if isinstance(mapping.get("target"), dict) else {}
    fields = mapping.get("fields") if isinstance(mapping.get("fields"), list) else []
    value_maps = document.get("value_maps") if isinstance(document.get("value_maps"), dict) else {}

    source_endpoint: dict[str, Any] = {"file": source_file, "key": _key_value(source_key)}
    target_endpoint: dict[str, Any] = {"file": target_file, "key": _key_value(target_key)}
    source_format = _format_for_file(source_file)
    target_format = _format_for_file(target_file)
    if source_format:
        source_endpoint["format"] = source_format
    if target_format:
        target_endpoint["format"] = target_format

    checks: list[dict[str, Any]] = [
        {
            "id": "record-coverage",
            "type": "record_coverage",
            "severity": "error",
            "allow_unexpected": False,
        }
    ]
    materiality_fields: dict[str, dict[str, Any]] = {}

    for index, field in enumerate(fields):
        if not isinstance(field, dict):
            continue
        transform = field.get("transform") if isinstance(field.get("transform"), dict) else {"type": "copy"}
        transform_type = str(transform.get("type", "copy"))
        source_ep = field.get("source") if isinstance(field.get("source"), dict) else {}
        target_ep = field.get("target") if isinstance(field.get("target"), dict) else {}
        source_field = source_ep.get("field")
        target_field = target_ep.get("field")
        if source_field and target_field and transform_type in {"copy", "lookup"}:
            criticality = _criticality(field)
            check: dict[str, Any] = {
                "id": _slug(field.get("id") or f"field-{index}", lower=True),
                "type": "field_match",
                "source": str(source_field),
                "target": str(target_field),
                "severity": "error" if criticality in {"high", "critical"} else "warning",
                "null_semantics": "empty_is_null",
            }
            if transform_type == "lookup":
                reference = transform.get("reference")
                if reference in value_maps and isinstance(value_maps[reference], dict):
                    check["map"] = value_maps[reference]
            checks.append(check)
            if criticality in {"high", "critical"}:
                materiality_fields[str(target_field)] = {"severity": "error", "critical": True}

    result: dict[str, Any] = {
        "version": 1,
        "object": {"type": str(target.get("object") or source.get("object") or "mapped-object")},
        "reconciliation": {
            "name": f'{mapping.get("id", "mapping")} generated reconciliation',
            "description": "Generated from Mapping as Code; only deterministic copy/lookup mappings become field checks.",
        },
        "source": source_endpoint,
        "target": target_endpoint,
        "checks": checks,
        "generated_from": {
            "tool": "mapping-as-code",
            "mapping_id": mapping.get("id"),
            "schema_version": document.get("schema_version"),
        },
    }
    if materiality_fields:
        result["materiality"] = {"fields": materiality_fields}
    return result
