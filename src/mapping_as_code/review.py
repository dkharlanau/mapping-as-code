from __future__ import annotations

import json
from collections import Counter
from typing import Any

from .governance import breaking_change_report, quality_scorecard, validation_report


_SEVERITY_RANK = {"info": 0, "warning": 1, "error": 2}


def _field_index(document: dict[str, Any]) -> dict[str, dict[str, Any]]:
    mapping = document.get("mapping") if isinstance(document.get("mapping"), dict) else {}
    fields = mapping.get("fields") if isinstance(mapping.get("fields"), list) else []
    result: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(fields):
        if not isinstance(item, dict):
            continue
        field_id = item.get("id")
        if not str(field_id or "").strip():
            target = item.get("target") if isinstance(item.get("target"), dict) else {}
            field_id = f"@target:{target.get('field', index)}"
        result[str(field_id)] = item
    return result


def _required_target(document: dict[str, Any], field: dict[str, Any] | None) -> bool:
    if not isinstance(field, dict):
        return False
    mapping = document.get("mapping") if isinstance(document.get("mapping"), dict) else {}
    target = mapping.get("target") if isinstance(mapping.get("target"), dict) else {}
    required = target.get("required_fields") if isinstance(target.get("required_fields"), list) else []
    field_target = field.get("target") if isinstance(field.get("target"), dict) else {}
    rules = field.get("rules") if isinstance(field.get("rules"), dict) else {}
    return bool(rules.get("required") is True or field_target.get("field") in required)


def _location(provenance: dict[str, Any] | None, field_id: str) -> Any:
    if not isinstance(provenance, dict):
        return None
    fields = provenance.get("fields") if isinstance(provenance.get("fields"), dict) else {}
    return fields.get(field_id)


def _field_snapshot(
    document: dict[str, Any],
    field: dict[str, Any] | None,
    *,
    field_id: str,
    provenance: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if not isinstance(field, dict):
        return None
    business = field.get("business") if isinstance(field.get("business"), dict) else {}
    return {
        "source": field.get("source"),
        "target": field.get("target"),
        "transform": field.get("transform"),
        "rules": field.get("rules"),
        "business": field.get("business"),
        "required_target": _required_target(document, field),
        "owner": business.get("owner"),
        "criticality": business.get("criticality"),
        "rationale": business.get("rationale"),
        "location": _location(provenance, field_id),
    }


def _value_map_changes_by_name(diff: dict[str, Any]) -> dict[str, dict[str, Any]]:
    value_maps = diff.get("value_maps") if isinstance(diff.get("value_maps"), dict) else {}
    result: dict[str, dict[str, Any]] = {}
    for name in value_maps.get("added", []):
        result[str(name)] = {"map": str(name), "change": "map_added"}
    for name in value_maps.get("removed", []):
        result[str(name)] = {"map": str(name), "change": "map_removed"}
    for item in value_maps.get("changed", []):
        if isinstance(item, dict) and item.get("map") is not None:
            result[str(item["map"])] = item
    return result


def _referenced_value_maps(snapshot: dict[str, Any] | None) -> set[str]:
    if not isinstance(snapshot, dict):
        return set()
    transform = snapshot.get("transform") if isinstance(snapshot.get("transform"), dict) else {}
    reference = transform.get("reference")
    return {str(reference)} if reference is not None else set()


def _highest_severity(events: list[dict[str, Any]]) -> str:
    severities = [str(item.get("severity", "info")) for item in events]
    return max(severities or ["info"], key=lambda value: _SEVERITY_RANK.get(value, 0))


def _functional_changes(
    old: dict[str, Any],
    new: dict[str, Any],
    changes: dict[str, Any],
    *,
    old_provenance: dict[str, Any] | None = None,
    new_provenance: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    diff = changes["diff"]
    old_index = _field_index(old)
    new_index = _field_index(new)
    field_ids = set(diff.get("added", [])) | set(diff.get("removed", []))
    field_ids.update(
        str(item["id"])
        for item in diff.get("changed", [])
        if isinstance(item, dict) and item.get("id") is not None
    )
    events_by_id: dict[str, list[dict[str, Any]]] = {}
    for event in changes.get("events", []):
        if event.get("kind") == "value_map":
            continue
        events_by_id.setdefault(str(event.get("id")), []).append(event)

    changed_value_maps = _value_map_changes_by_name(diff)
    changed_value_map_names = set(changed_value_maps)
    for field_id in sorted(set(old_index) | set(new_index)):
        before_field = old_index.get(field_id)
        after_field = new_index.get(field_id)
        before_snapshot = _field_snapshot(
            old, before_field, field_id=field_id, provenance=old_provenance
        )
        after_snapshot = _field_snapshot(
            new, after_field, field_id=field_id, provenance=new_provenance
        )
        references = _referenced_value_maps(before_snapshot) | _referenced_value_maps(after_snapshot)
        if references & changed_value_map_names:
            field_ids.add(field_id)

    value_map_events_by_name: dict[str, list[dict[str, Any]]] = {}
    for event in changes.get("events", []):
        if event.get("kind") == "value_map" and event.get("map") is not None:
            value_map_events_by_name.setdefault(str(event["map"]), []).append(event)

    result: list[dict[str, Any]] = []
    for field_id in sorted(field_ids):
        before = _field_snapshot(
            old, old_index.get(field_id), field_id=field_id, provenance=old_provenance
        )
        after = _field_snapshot(
            new, new_index.get(field_id), field_id=field_id, provenance=new_provenance
        )
        events = events_by_id.get(field_id, [])
        change_types = sorted({str(item.get("kind", "change")) for item in events})
        if not change_types:
            if field_id in diff.get("added", []):
                change_types = ["added"]
            elif field_id in diff.get("removed", []):
                change_types = ["removed"]

        references = _referenced_value_maps(before) | _referenced_value_maps(after)
        impacted_map_names = [name for name in sorted(references) if name in changed_value_maps]
        value_map_impacts = [changed_value_maps[name] for name in impacted_map_names]
        value_map_events = [
            event
            for name in impacted_map_names
            for event in value_map_events_by_name.get(name, [])
        ]
        if value_map_impacts and "value_map" not in change_types:
            change_types.append("value_map")
        reasons = list(change_types)
        if value_map_impacts:
            reasons.append("referenced_value_map_changed")
        result.append(
            {
                "id": field_id,
                "severity": _highest_severity([*events, *value_map_events]),
                "change_types": change_types,
                "before": before,
                "after": after,
                "value_map_impacts": value_map_impacts,
                "decision": {"status": "review_required", "reasons": reasons},
            }
        )
    return result


def review_report(
    old: dict[str, Any],
    new: dict[str, Any],
    policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    baseline_quality = quality_scorecard(old)
    current_validation = validation_report(new, policy)
    changes = breaking_change_report(old, new, policy)
    current_quality = current_validation["quality"]
    dimensions = sorted(set(baseline_quality["dimensions"]) | set(current_quality["dimensions"]))
    dimension_delta = {
        name: round(float(current_quality["dimensions"].get(name, 0)) - float(baseline_quality["dimensions"].get(name, 0)), 2)
        for name in dimensions
    }
    score_delta = round(float(current_quality["score"]) - float(baseline_quality["score"]), 2)
    quality_policy = policy.get("quality", {}) if isinstance(policy, dict) and isinstance(policy.get("quality"), dict) else {}
    max_regression = quality_policy.get("max_score_regression")
    regression_passed = max_regression is None or score_delta >= -float(max_regression)
    passed = bool(current_validation["valid"] and changes["passed"] and regression_passed)
    return {
        "review_version": 1,
        "mapping_id": current_validation.get("mapping_id"),
        "policy": current_validation["policy"],
        "baseline": {
            "document_sha256": changes["old_document_sha256"],
            "quality": baseline_quality,
        },
        "current": {
            "document_sha256": changes["new_document_sha256"],
            "validation": current_validation,
        },
        "quality_delta": {
            "score": score_delta,
            "dimensions": dimension_delta,
            "gate": {
                "max_score_regression": max_regression,
                "passed": regression_passed,
            },
        },
        "changes": changes,
        "passed": passed,
    }


def _append_limited(lines: list[str], items: list[dict[str, Any]], *, limit: int, formatter) -> None:
    visible = items[:limit]
    for item in visible:
        lines.append(formatter(item))
    remaining = len(items) - len(visible)
    if remaining > 0:
        lines.append(f"- … **{remaining} more** not shown in the compact summary.")


def review_markdown(report: dict[str, Any], *, max_items: int = 20) -> str:
    if max_items < 1:
        raise ValueError("max_items must be at least 1")
    delta = float(report["quality_delta"]["score"])
    delta_text = f"+{delta:.2f}" if delta > 0 else f"{delta:.2f}"
    current = report["current"]["validation"]
    events = report["changes"]["events"]
    diagnostics = current["diagnostics"]
    regression_gate = report["quality_delta"]["gate"]
    severity_counts = Counter(str(item.get("severity", "info")) for item in events)
    kind_counts = Counter(str(item.get("kind", "change")) for item in events)
    diagnostic_counts = Counter(str(item.get("severity", "info")) for item in diagnostics)
    lines = [
        "## Mapping as Code review",
        "",
        f"**Result:** {'PASS' if report['passed'] else 'FAIL'}",
        "",
        "| Metric | Baseline | Current | Delta |",
        "| --- | ---: | ---: | ---: |",
        f"| Quality | {report['baseline']['quality']['score']:.2f} | {current['quality']['score']:.2f} | {delta_text} |",
        f"| Required target coverage | {report['baseline']['quality']['dimensions']['required_target_coverage']:.2f} | {current['quality']['dimensions']['required_target_coverage']:.2f} | {report['quality_delta']['dimensions']['required_target_coverage']:+.2f} |",
        "",
        f"Policy: `{report['policy']['name']}`",
        "",
        "**Change summary:** "
        f"{len(events)} events · {severity_counts.get('error', 0)} errors · "
        f"{severity_counts.get('warning', 0)} warnings · {severity_counts.get('info', 0)} info",
        "",
    ]
    if kind_counts:
        kind_text = " · ".join(f"{kind}: {count}" for kind, count in sorted(kind_counts.items()))
        lines.extend([f"Kinds: {kind_text}", ""])
    if regression_gate["max_score_regression"] is not None:
        lines.extend(
            [
                f"Quality regression gate: **{'PASS' if regression_gate['passed'] else 'FAIL'}** "
                f"(maximum drop {float(regression_gate['max_score_regression']):.2f})",
                "",
            ]
        )
    lines.extend(["### Change events", ""])
    if events:
        _append_limited(
            lines,
            events,
            limit=max_items,
            formatter=lambda event: f"- **{event['severity'].upper()}** `{event['id']}` — {event['kind']}",
        )
    else:
        lines.append("No semantic mapping changes.")
    lines.extend(["", "### Current diagnostics", ""])
    if diagnostics:
        lines.append(
            f"Diagnostics: {diagnostic_counts.get('error', 0)} errors · "
            f"{diagnostic_counts.get('warning', 0)} warnings · {diagnostic_counts.get('info', 0)} info"
        )
        lines.append("")
        _append_limited(
            lines,
            diagnostics,
            limit=max_items,
            formatter=lambda item: f"- **{item['severity'].upper()}** `{item['code']}` — {item['message']}",
        )
    else:
        lines.append("No diagnostics.")
    lines.extend(
        [
            "",
            f"Baseline SHA: `{report['baseline']['document_sha256']}`",
            f"Current SHA: `{report['current']['document_sha256']}`",
            "",
        ]
    )
    return "\n".join(lines)
