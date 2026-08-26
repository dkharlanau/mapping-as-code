from __future__ import annotations

from collections import Counter
from typing import Any

from .governance import breaking_change_report, quality_scorecard, validation_report


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
