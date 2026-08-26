from __future__ import annotations

import hashlib
import re
from copy import deepcopy
from pathlib import Path
from typing import Any

from .core import validate_document
from .governance import canonical_hash
from .io import load_document

_NAMESPACE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


class CompositionError(ValueError):
    pass


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _resolve_within(root: Path, relative: str, *, label: str) -> Path:
    candidate = Path(relative)
    if candidate.is_absolute():
        raise CompositionError(f"{label} must be a relative path")
    root_resolved = root.resolve()
    resolved = (root_resolved / candidate).resolve()
    try:
        resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise CompositionError(f"{label} escapes the composition directory: {relative}") from exc
    if not resolved.is_file():
        raise CompositionError(f"{label} does not exist or is not a file: {relative}")
    return resolved


def _unique_extend(target: list[Any], values: list[Any]) -> None:
    seen = set(target)
    for value in values:
        if value not in seen:
            target.append(value)
            seen.add(value)


def _namespace_fragment(fragment: dict[str, Any], namespace: str | None) -> dict[str, Any]:
    result = deepcopy(fragment)
    if namespace is None:
        return result
    if not _NAMESPACE_RE.fullmatch(namespace):
        raise CompositionError(f"invalid fragment namespace: {namespace!r}")

    local_maps = result.get("value_maps") if isinstance(result.get("value_maps"), dict) else {}
    map_renames = {str(name): f"{namespace}:{name}" for name in local_maps}
    result["value_maps"] = {map_renames[str(name)]: value for name, value in local_maps.items()}

    fields = result.get("fields") if isinstance(result.get("fields"), list) else []
    for field in fields:
        if not isinstance(field, dict):
            continue
        field_id = str(field.get("id") or "").strip()
        if field_id:
            field["id"] = f"{namespace}:{field_id}"
        transform = field.get("transform") if isinstance(field.get("transform"), dict) else None
        if transform and transform.get("type") == "lookup":
            reference = str(transform.get("reference") or "")
            if reference in map_renames:
                transform["reference"] = map_renames[reference]
    return result


def _check_fragment(fragment: dict[str, Any], *, path: str) -> None:
    if fragment.get("fragment_version") != 1:
        raise CompositionError(f"{path}: fragment_version must be 1")
    fields = fragment.get("fields")
    if not isinstance(fields, list) or not fields:
        raise CompositionError(f"{path}: fields must be a non-empty array")
    for index, field in enumerate(fields):
        if not isinstance(field, dict):
            raise CompositionError(f"{path}: fields[{index}] must be an object")
        if not str(field.get("id") or "").strip():
            raise CompositionError(f"{path}: fields[{index}].id is required")
        if not isinstance(field.get("target"), dict) or not str(field["target"].get("field") or "").strip():
            raise CompositionError(f"{path}: fields[{index}].target.field is required")


def compose_manifest(manifest_path: str | Path) -> tuple[dict[str, Any], dict[str, Any]]:
    manifest_file = Path(manifest_path).resolve()
    if not manifest_file.is_file():
        raise CompositionError(f"composition manifest not found: {manifest_path}")
    manifest = load_document(manifest_file)
    if manifest.get("composition_version") != 1:
        raise CompositionError("composition_version must be 1")
    base_ref = str(manifest.get("base") or "").strip()
    if not base_ref:
        raise CompositionError("composition manifest requires base")
    fragments_spec = manifest.get("fragments")
    if not isinstance(fragments_spec, list) or not fragments_spec:
        raise CompositionError("composition manifest requires a non-empty fragments array")

    root = manifest_file.parent
    base_path = _resolve_within(root, base_ref, label="base")
    result = deepcopy(load_document(base_path))
    mapping = result.get("mapping") if isinstance(result.get("mapping"), dict) else None
    if mapping is None:
        raise CompositionError(f"{base_ref}: base document must contain mapping")
    base_fields = mapping.get("fields")
    if not isinstance(base_fields, list):
        raise CompositionError(f"{base_ref}: mapping.fields must be an array")
    result_maps = result.get("value_maps") if isinstance(result.get("value_maps"), dict) else {}
    result["value_maps"] = deepcopy(result_maps)

    existing_ids = {str(item.get("id")) for item in base_fields if isinstance(item, dict) and item.get("id") is not None}
    report_fragments: list[dict[str, Any]] = []

    for index, spec in enumerate(fragments_spec):
        if not isinstance(spec, dict):
            raise CompositionError(f"fragments[{index}] must be an object")
        relative = str(spec.get("path") or "").strip()
        if not relative:
            raise CompositionError(f"fragments[{index}].path is required")
        namespace_value = spec.get("namespace")
        namespace = str(namespace_value).strip() if namespace_value is not None else None
        fragment_path = _resolve_within(root, relative, label=f"fragments[{index}].path")
        raw_fragment = load_document(fragment_path)
        _check_fragment(raw_fragment, path=relative)
        fragment = _namespace_fragment(raw_fragment, namespace)

        fields = fragment["fields"]
        for field in fields:
            field_id = str(field["id"])
            if field_id in existing_ids:
                raise CompositionError(f"duplicate field mapping id after composition: {field_id}")
            existing_ids.add(field_id)
            base_fields.append(deepcopy(field))

        fragment_maps = fragment.get("value_maps") if isinstance(fragment.get("value_maps"), dict) else {}
        for name, value in fragment_maps.items():
            if name in result["value_maps"] and result["value_maps"][name] != value:
                raise CompositionError(f"conflicting value map after composition: {name}")
            result["value_maps"][name] = deepcopy(value)

        required = fragment.get("required_fields") if isinstance(fragment.get("required_fields"), dict) else {}
        for side in ("source", "target"):
            values = required.get(side)
            if values is None:
                continue
            if not isinstance(values, list) or any(not str(item).strip() for item in values):
                raise CompositionError(f"{relative}: required_fields.{side} must be an array of non-empty strings")
            endpoint = mapping.get(side) if isinstance(mapping.get(side), dict) else None
            if endpoint is None:
                raise CompositionError(f"{base_ref}: mapping.{side} must be an object")
            existing_required = endpoint.get("required_fields")
            if existing_required is None:
                endpoint["required_fields"] = []
                existing_required = endpoint["required_fields"]
            if not isinstance(existing_required, list):
                raise CompositionError(f"{base_ref}: mapping.{side}.required_fields must be an array")
            _unique_extend(existing_required, values)

        report_fragments.append(
            {
                "path": relative,
                "namespace": namespace,
                "sha256": _file_sha256(fragment_path),
                "field_mappings": len(fields),
                "value_maps": len(fragment_maps),
            }
        )

    diagnostics = validate_document(result)
    errors = [item for item in diagnostics if item.severity == "error"]
    if errors:
        detail = "; ".join(f"{item.code} [{item.path}]: {item.message}" for item in errors[:10])
        remaining = len(errors) - min(len(errors), 10)
        if remaining > 0:
            detail += f"; … {remaining} more"
        raise CompositionError("composed mapping is invalid: " + detail)

    report = {
        "composition_version": 1,
        "manifest": {"path": manifest_file.name, "sha256": _file_sha256(manifest_file)},
        "base": {"path": base_ref, "sha256": _file_sha256(base_path)},
        "fragments": report_fragments,
        "result": {
            "mapping_id": mapping.get("id"),
            "field_mappings": len(base_fields),
            "value_maps": len(result["value_maps"]),
            "canonical_sha256": canonical_hash(result),
        },
    }
    return result, report
