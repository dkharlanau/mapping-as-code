from __future__ import annotations

from typing import Any

from .adapters import (
    to_enterprise_change_graph,
    to_reconciliation,
    to_transformation_graph,
    to_visual_workbench,
)
from .artifacts import release_bundle
from .change_projection import to_enterprise_change_transition
from .contracts import TARGET_CONTRACTS
from .governance import canonical_hash
from .interface_binding import bind_interface_contract


def _artifact(kind: str, value: dict[str, Any], contract: str | None = None) -> dict[str, Any]:
    item: dict[str, Any] = {
        "kind": kind,
        "sha256": canonical_hash(value),
        "document": value,
    }
    if contract:
        item["contract"] = TARGET_CONTRACTS[contract]
    return item


def ecosystem_bundle(
    mapping_document: dict[str, Any],
    *,
    source_name: str,
    source_hash: str,
    policy: dict[str, Any] | None = None,
    baseline: dict[str, Any] | None = None,
    reconciliation: dict[str, Any] | None = None,
    interface_document: dict[str, Any] | None = None,
    mapping_uri: str | None = None,
    revision: str | None = None,
) -> dict[str, Any]:
    mapping = mapping_document.get("mapping") if isinstance(mapping_document.get("mapping"), dict) else {}
    mapping_id = mapping.get("id")
    if not mapping_id:
        raise ValueError("mapping.id is required")

    release = release_bundle(
        mapping_document,
        source_name=source_name,
        source_hash=source_hash,
        policy=policy,
    )
    artifacts: dict[str, Any] = {
        "mapping-release": _artifact("mapping-release", release),
        "transformation-graph": _artifact(
            "transformation-graph",
            to_transformation_graph(mapping_document),
            "transformation-graph",
        ),
        "enterprise-change-graph": _artifact(
            "enterprise-change-graph",
            to_enterprise_change_graph(mapping_document),
            "enterprise-change-graph",
        ),
        "visual-workbench": _artifact(
            "visual-workbench",
            to_visual_workbench(mapping_document),
            "visual-workbench",
        ),
    }

    if baseline is not None:
        artifacts["enterprise-change-transition"] = _artifact(
            "enterprise-change-transition",
            to_enterprise_change_transition(baseline, mapping_document),
            "enterprise-change-graph",
        )

    if reconciliation is not None:
        required = ("source_file", "target_file", "source_key", "target_key")
        missing = [name for name in required if not reconciliation.get(name)]
        if missing:
            raise ValueError("reconciliation bundle configuration missing: " + ", ".join(missing))
        artifacts["reconciliation-as-code"] = _artifact(
            "reconciliation-as-code",
            to_reconciliation(
                mapping_document,
                source_file=str(reconciliation["source_file"]),
                target_file=str(reconciliation["target_file"]),
                source_key=reconciliation["source_key"],
                target_key=reconciliation["target_key"],
            ),
            "reconciliation-as-code",
        )

    if interface_document is not None:
        if not mapping_uri:
            raise ValueError("mapping_uri is required when interface_document is supplied")
        artifacts["interface-as-code"] = _artifact(
            "interface-as-code",
            bind_interface_contract(
                interface_document,
                mapping_document,
                mapping_uri=mapping_uri,
                revision=revision,
            ),
            "interface-as-code",
        )

    return {
        "ecosystem_bundle_version": 1,
        "mapping_id": mapping_id,
        "mapping_canonical_sha256": canonical_hash(mapping_document),
        "artifacts": artifacts,
    }
