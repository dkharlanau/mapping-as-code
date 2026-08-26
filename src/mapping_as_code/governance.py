from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import Any

from .core import Diagnostic, diff_documents, mapping_summary, validate_document


_ALLOWED_CRITICALITIES = ("low", "medium", "high", "critical")
_ALLOWED_SEVERITIES = ("ignore", "info", "warning", "error")

DEFAULT_POLICY: dict[str, Any] = {
    "version": 1,
    "name": "baseline",
    "requirements": {
        "owner_required_for": ["high", "critical"],
        "rationale_required_for": ["high", "critical"],
        "criticality_required": False,
        "title_required": True,
    },
    "quality": {"minimum_score": 0, "max_warnings": None},
    "breaking_changes": {
        "removed": "error",
        "source": "warning",
        "target": "error",
        "transform": "error",
        "rules": "warning",
        "business": "warning",
    },
}


def canonical_hash(document: dict[str, Any]) -> str:
    payload = json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def normalize_policy(policy: dict[str, Any] | None) -> dict[str, Any]:
    merged = deepcopy(DEFAULT_POLICY)
    if policy is None:
        return merged
    if not isinstance(policy, dict):
        raise ValueError("policy must be an object")
    if policy.get("version", 1) != 1:
        raise ValueError("unsupported policy version")
    for section in ("requirements", "quality", "breaking_changes"):
        value = policy.get(section)
        if value is not None:
            if not isinstance(value, dict):
                raise ValueError(f"policy.{section} must be an object")
            merged[section].update(value)
    if policy.get("name"):
        merged["name"] = str(policy["name"])
    merged["version"] = 1
    return merged


def _field_maps(document: dict[str, Any]) -> list[dict[str, Any]]:
    mapping = document.get("mapping") if isinstance(document.get("mapping"), dict) else {}
    fields = mapping.get("fields") if isinstance(mapping.get("fields"), list) else []
    return [item for item in fields if isinstance(item, dict)]


def policy_diagnostics(document: dict[str, Any], policy: dict[str, Any] | None = None) -> list[Diagnostic]:
    policy = normalize_policy(policy)
    requirements = policy["requirements"]
    diagnostics: list[Diagnostic] = []
    mapping = document.get("mapping") if isinstance(document.get("mapping"), dict) else {}

    if requirements.get("title_required", False) and not str(mapping.get("title") or "").strip():
        diagnostics.append(Diagnostic("policy.mapping.title", "mapping title is required by policy", "mapping.title"))

    owner_required_for = set(requirements.get("owner_required_for") or [])
    rationale_required_for = set(requirements.get("rationale_required_for") or [])
    criticality_required = bool(requirements.get("criticality_required", False))

    for index, field_map in enumerate(_field_maps(document)):
        business = field_map.get("business") if isinstance(field_map.get("business"), dict) else {}
        criticality = business.get("criticality")
        path = f"mapping.fields[{index}].business"
        if criticality is not None and criticality not in _ALLOWED_CRITICALITIES:
            diagnostics.append(
                Diagnostic(
                    "policy.criticality.invalid",
                    f"criticality '{criticality}' is not one of {', '.join(_ALLOWED_CRITICALITIES)}",
                    f"{path}.criticality",
                )
            )
            continue
        if criticality_required and not criticality:
            diagnostics.append(Diagnostic("policy.criticality.missing", "criticality is required by policy", f"{path}.criticality"))
        if criticality in owner_required_for and not str(business.get("owner") or "").strip():
            diagnostics.append(
                Diagnostic(
                    "policy.owner.missing",
                    f"owner is required for {criticality} mappings",
                    f"{path}.owner",
                )
            )
        if criticality in rationale_required_for and not str(business.get("rationale") or "").strip():
            diagnostics.append(
                Diagnostic(
                    "policy.rationale.missing",
                    f"rationale is required for {criticality} mappings",
                    f"{path}.rationale",
                )
            )
    return diagnostics


def quality_scorecard(document: dict[str, Any]) -> dict[str, Any]:
    diagnostics = validate_document(document)
    summary = mapping_summary(document)
    fields = _field_maps(document)
    count = len(fields)
    errors = sum(1 for item in diagnostics if item.severity == "error")

    owner_count = 0
    rationale_count = 0
    criticality_count = 0
    stable_id_count = 0
    for item in fields:
        business = item.get("business") if isinstance(item.get("business"), dict) else {}
        owner_count += int(bool(str(business.get("owner") or "").strip()))
        rationale_count += int(bool(str(business.get("rationale") or "").strip()))
        criticality_count += int(business.get("criticality") in _ALLOWED_CRITICALITIES)
        stable_id_count += int(bool(str(item.get("id") or "").strip()))

    def ratio(value: int) -> float:
        return 1.0 if count == 0 else value / count

    dimensions = {
        "validity": max(0.0, 35.0 - errors * 10.0),
        "required_target_coverage": round(float(summary.get("coverage", 0.0)) * 25.0, 2),
        "ownership": round(ratio(owner_count) * 15.0, 2),
        "rationale": round(ratio(rationale_count) * 10.0, 2),
        "criticality": round(ratio(criticality_count) * 10.0, 2),
        "stable_ids": round(ratio(stable_id_count) * 5.0, 2),
    }
    score = round(sum(dimensions.values()), 2)
    return {
        "score": score,
        "maximum": 100.0,
        "dimensions": dimensions,
        "counts": {
            "field_mappings": count,
            "owners": owner_count,
            "rationales": rationale_count,
            "criticalities": criticality_count,
            "stable_ids": stable_id_count,
            "validation_errors": errors,
        },
    }


def validation_report(document: dict[str, Any], policy: dict[str, Any] | None = None) -> dict[str, Any]:
    normalized = normalize_policy(policy)
    base = validate_document(document)
    governed = policy_diagnostics(document, normalized)
    diagnostics = [*base, *governed]
    quality = quality_scorecard(document)
    warning_count = sum(1 for item in diagnostics if item.severity == "warning")
    error_count = sum(1 for item in diagnostics if item.severity == "error")
    minimum_score = float(normalized["quality"].get("minimum_score") or 0)
    max_warnings = normalized["quality"].get("max_warnings")
    quality_gate = quality["score"] >= minimum_score
    warnings_gate = max_warnings is None or warning_count <= int(max_warnings)
    valid = error_count == 0 and quality_gate and warnings_gate
    return {
        "report_version": 1,
        "mapping_id": mapping_summary(document).get("mapping_id"),
        "document_sha256": canonical_hash(document),
        "policy": {"name": normalized["name"], "version": normalized["version"]},
        "summary": mapping_summary(document),
        "quality": quality,
        "diagnostics": [item.as_dict() for item in diagnostics],
        "gates": {
            "no_errors": error_count == 0,
            "minimum_quality_score": {"threshold": minimum_score, "passed": quality_gate},
            "max_warnings": {"threshold": max_warnings, "actual": warning_count, "passed": warnings_gate},
        },
        "valid": valid,
    }


def _severity(policy: dict[str, Any], kind: str) -> str:
    value = str(policy["breaking_changes"].get(kind, "warning"))
    if value not in _ALLOWED_SEVERITIES:
        raise ValueError(f"unsupported breaking-change severity '{value}' for {kind}")
    return value


def breaking_change_report(
    old: dict[str, Any], new: dict[str, Any], policy: dict[str, Any] | None = None
) -> dict[str, Any]:
    normalized = normalize_policy(policy)
    diff = diff_documents(old, new)
    events: list[dict[str, Any]] = []

    for field_id in diff["removed"]:
        severity = _severity(normalized, "removed")
        if severity != "ignore":
            events.append({"id": field_id, "kind": "removed", "severity": severity})
    for field_id in diff["added"]:
        events.append({"id": field_id, "kind": "added", "severity": "info"})
    for changed in diff["changed"]:
        for section, values in changed["changes"].items():
            severity = _severity(normalized, section)
            if severity == "ignore":
                continue
            events.append(
                {
                    "id": changed["id"],
                    "kind": section,
                    "severity": severity,
                    "before": values.get("before"),
                    "after": values.get("after"),
                }
            )

    blocked = any(event["severity"] == "error" for event in events)
    return {
        "report_version": 1,
        "old_document_sha256": canonical_hash(old),
        "new_document_sha256": canonical_hash(new),
        "policy": {"name": normalized["name"], "version": normalized["version"]},
        "diff": diff,
        "events": events,
        "breaking": blocked,
        "passed": not blocked,
    }
