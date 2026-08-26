from __future__ import annotations

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
    passed = bool(current_validation["valid"] and changes["passed"])
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
        "quality_delta": {"score": score_delta, "dimensions": dimension_delta},
        "changes": changes,
        "passed": passed,
    }


def review_markdown(report: dict[str, Any]) -> str:
    delta = float(report["quality_delta"]["score"])
    delta_text = f"+{delta:.2f}" if delta > 0 else f"{delta:.2f}"
    current = report["current"]["validation"]
    events = report["changes"]["events"]
    errors = [item for item in events if item["severity"] == "error"]
    warnings = [item for item in events if item["severity"] == "warning"]
    diagnostics = current["diagnostics"]
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
        "### Change events",
        "",
    ]
    if events:
        for event in events:
            lines.append(f"- **{event['severity'].upper()}** `{event['id']}` — {event['kind']}")
    else:
        lines.append("No semantic mapping changes.")
    lines.extend(["", "### Current diagnostics", ""])
    if diagnostics:
        for item in diagnostics:
            lines.append(f"- **{item['severity'].upper()}** `{item['code']}` — {item['message']}")
    else:
        lines.append("No diagnostics.")
    lines.extend(
        [
            "",
            f"Breaking errors: **{len(errors)}** · Breaking warnings: **{len(warnings)}**",
            "",
            f"Baseline SHA: `{report['baseline']['document_sha256']}`",
            f"Current SHA: `{report['current']['document_sha256']}`",
            "",
        ]
    )
    return "\n".join(lines)
