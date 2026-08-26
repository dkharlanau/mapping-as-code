from __future__ import annotations

from typing import Any

from .governance import validation_report


def sarif_report(
    document: dict[str, Any],
    *,
    artifact_uri: str,
    policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Render governance diagnostics as SARIF without inventing line locations."""
    report = validation_report(document, policy)
    diagnostics = report["diagnostics"]
    rules: dict[str, dict[str, Any]] = {}
    results: list[dict[str, Any]] = []
    for diagnostic in diagnostics:
        code = str(diagnostic.get("code") or "mapping.diagnostic")
        severity = str(diagnostic.get("severity") or "warning")
        level = "error" if severity == "error" else "warning" if severity == "warning" else "note"
        rules.setdefault(
            code,
            {
                "id": code,
                "name": code.replace(".", "_"),
                "shortDescription": {"text": str(diagnostic.get("message") or code)},
                "properties": {"tags": ["mapping-as-code", "governance"]},
            },
        )
        results.append(
            {
                "ruleId": code,
                "level": level,
                "message": {
                    "text": f"{diagnostic.get('path', '')}: {diagnostic.get('message', '')}".strip(": ")
                },
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {"uri": artifact_uri}
                        }
                    }
                ],
                "properties": {
                    "mappingPath": diagnostic.get("path", ""),
                    "severity": severity,
                },
            }
        )
    return {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "Mapping as Code",
                        "version": "0.5.0",
                        "informationUri": "https://github.com/dkharlanau/mapping-as-code",
                        "rules": list(rules.values()),
                    }
                },
                "results": results,
                "properties": {
                    "mappingId": report.get("mapping_id"),
                    "documentSha256": report.get("document_sha256"),
                    "policy": report.get("policy"),
                    "valid": report.get("valid"),
                },
            }
        ],
    }
