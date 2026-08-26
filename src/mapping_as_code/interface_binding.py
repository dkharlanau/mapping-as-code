from __future__ import annotations

from copy import deepcopy
from typing import Any

from .governance import canonical_hash


def _endpoint(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _norm(value: Any) -> str:
    return str(value or "").strip().casefold()


def _endpoint_mismatches(interface_document: dict[str, Any], mapping_document: dict[str, Any]) -> list[str]:
    interface = interface_document.get("interface") if isinstance(interface_document.get("interface"), dict) else {}
    mapping = mapping_document.get("mapping") if isinstance(mapping_document.get("mapping"), dict) else {}
    pairs = (
        ("source.system", _endpoint(interface.get("source")).get("system"), _endpoint(mapping.get("source")).get("system")),
        ("source.object", _endpoint(interface.get("source")).get("object"), _endpoint(mapping.get("source")).get("object")),
        ("target.system", _endpoint(interface.get("target")).get("system"), _endpoint(mapping.get("target")).get("system")),
        ("target.object", _endpoint(interface.get("target")).get("object"), _endpoint(mapping.get("target")).get("object")),
    )
    mismatches: list[str] = []
    for name, interface_value, mapping_value in pairs:
        if interface_value is None or mapping_value is None:
            continue
        if _norm(interface_value) != _norm(mapping_value):
            mismatches.append(f"{name}: interface={interface_value!r}, mapping={mapping_value!r}")
    return mismatches


def bind_interface_contract(
    interface_document: dict[str, Any],
    mapping_document: dict[str, Any],
    *,
    mapping_uri: str,
    revision: str | None = None,
    allow_endpoint_mismatch: bool = False,
) -> dict[str, Any]:
    """Attach a Mapping as Code artifact reference to an existing Interface as Code v1.0 contract.

    Mapping as Code intentionally does not invent interface trigger, delivery, retry, monitoring,
    reconciliation, or security semantics. This function only binds an existing interface contract
    to the exact mapping semantics it uses.
    """
    if str(interface_document.get("version")) != "1.0":
        raise ValueError("Interface as Code binding currently supports version '1.0' only")
    if not isinstance(interface_document.get("interface"), dict):
        raise ValueError("interface document must contain an interface object")
    mapping = mapping_document.get("mapping")
    if not isinstance(mapping, dict) or not str(mapping.get("id") or "").strip():
        raise ValueError("mapping document must contain mapping.id")
    if not str(mapping_uri or "").strip():
        raise ValueError("mapping_uri must not be empty")

    mismatches = _endpoint_mismatches(interface_document, mapping_document)
    if mismatches and not allow_endpoint_mismatch:
        raise ValueError("interface/mapping endpoint mismatch: " + "; ".join(mismatches))

    bound = deepcopy(interface_document)
    mapping_section = bound.get("mapping") if isinstance(bound.get("mapping"), dict) else {}
    mapping_section = deepcopy(mapping_section)
    mapping_section["ref"] = {
        "kind": "mapping-as-code",
        "uri": mapping_uri,
        "sha256": canonical_hash(mapping_document),
    }
    if revision:
        mapping_section["ref"]["revision"] = str(revision)
    if not mapping_section.get("profile"):
        mapping_section["profile"] = str(mapping.get("id"))
    bound["mapping"] = mapping_section
    return bound
