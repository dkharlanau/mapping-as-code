from __future__ import annotations

from copy import deepcopy
from typing import Any

from .adapters import _graph_id, to_enterprise_change_graph
from .core import diff_documents
from .governance import canonical_hash


def _mapping_id(document: dict[str, Any]) -> str:
    mapping = document.get("mapping") if isinstance(document.get("mapping"), dict) else {}
    value = str(mapping.get("id") or "").strip()
    if not value:
        raise ValueError("mapping.id is required for change projection")
    return value


def _mapping_title(document: dict[str, Any]) -> str:
    mapping = document.get("mapping") if isinstance(document.get("mapping"), dict) else {}
    return str(mapping.get("title") or mapping.get("id") or "Mapping")


def _edge_key(edge: dict[str, Any]) -> tuple[str, str, str]:
    return str(edge.get("source")), str(edge.get("target")), str(edge.get("relation"))


def to_enterprise_change_transition(
    old: dict[str, Any],
    new: dict[str, Any],
    *,
    change_id: str | None = None,
) -> dict[str, Any]:
    """Build a transition graph whose change seeds are affected stable mapping-rule nodes.

    Old-only nodes/edges remain in the transition graph and are marked removed. This keeps
    removed mapping rules traversable for impact analysis instead of losing their previous
    dependencies when only the new snapshot is projected.
    """
    old_mapping_id = _mapping_id(old)
    new_mapping_id = _mapping_id(new)
    if old_mapping_id != new_mapping_id:
        raise ValueError(
            f"change projection requires the same mapping.id; old={old_mapping_id!r}, new={new_mapping_id!r}"
        )

    old_graph = to_enterprise_change_graph(old)
    new_graph = to_enterprise_change_graph(new)
    diff = diff_documents(old, new)

    old_nodes = {str(node["id"]): deepcopy(node) for node in old_graph["nodes"]}
    new_nodes = {str(node["id"]): deepcopy(node) for node in new_graph["nodes"]}
    nodes: dict[str, dict[str, Any]] = {}
    for node_id, node in old_nodes.items():
        if node_id not in new_nodes:
            metadata = node.get("metadata") if isinstance(node.get("metadata"), dict) else {}
            node["metadata"] = {**metadata, "transition_status": "removed"}
        nodes[node_id] = node
    for node_id, node in new_nodes.items():
        if node_id not in old_nodes:
            metadata = node.get("metadata") if isinstance(node.get("metadata"), dict) else {}
            node["metadata"] = {**metadata, "transition_status": "added"}
        nodes[node_id] = node

    old_edges = {_edge_key(edge): deepcopy(edge) for edge in old_graph["edges"]}
    new_edges = {_edge_key(edge): deepcopy(edge) for edge in new_graph["edges"]}
    edges: dict[tuple[str, str, str], dict[str, Any]] = {}
    for key, edge in old_edges.items():
        if key not in new_edges:
            metadata = edge.get("metadata") if isinstance(edge.get("metadata"), dict) else {}
            edge["metadata"] = {**metadata, "transition_status": "removed"}
        edges[key] = edge
    for key, edge in new_edges.items():
        if key not in old_edges:
            metadata = edge.get("metadata") if isinstance(edge.get("metadata"), dict) else {}
            edge["metadata"] = {**metadata, "transition_status": "added"}
        edges[key] = edge

    added = set(diff["added"])
    removed = set(diff["removed"])
    changed = {str(item["id"]) for item in diff["changed"]}
    affected = sorted(added | removed | changed)
    seeds = [_graph_id("mapping", new_mapping_id, field_id) for field_id in affected]

    for field_id in affected:
        node_id = _graph_id("mapping", new_mapping_id, field_id)
        node = nodes.get(node_id)
        if not node:
            continue
        if field_id in added:
            status = "added"
        elif field_id in removed:
            status = "removed"
        else:
            status = "changed"
        metadata = node.get("metadata") if isinstance(node.get("metadata"), dict) else {}
        node["metadata"] = {**metadata, "transition_status": status}

    result: dict[str, Any] = {
        "version": 1,
        "metadata": {
            "source": "mapping-as-code",
            "projection": "mapping-transition",
            "mapping_id": new_mapping_id,
            "old_document_sha256": canonical_hash(old),
            "new_document_sha256": canonical_hash(new),
        },
        "nodes": list(nodes.values()),
        "edges": list(edges.values()),
    }
    if seeds:
        result["changes"] = [
            {
                "id": change_id or f"mapping-revision:{new_mapping_id}",
                "title": f"Mapping revision: {_mapping_title(new)}",
                "description": "Semantic Mapping as Code revision projected as impact-analysis seeds.",
                "kind": "mapping-revision",
                "seeds": seeds,
                "metadata": {
                    "added": sorted(added),
                    "removed": sorted(removed),
                    "changed": sorted(changed),
                },
                "provenance": "mapping-as-code",
            }
        ]
    return result
