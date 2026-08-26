from __future__ import annotations

from typing import Any

from .governance import validation_report


def _escape_data(value: Any) -> str:
    return str(value).replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def _escape_property(value: Any) -> str:
    return _escape_data(value).replace(":", "%3A").replace(",", "%2C")


def github_annotations(
    document: dict[str, Any],
    *,
    file_path: str,
    policy: dict[str, Any] | None = None,
) -> list[str]:
    report = validation_report(document, policy)
    lines: list[str] = []
    for diagnostic in report["diagnostics"]:
        severity = diagnostic.get("severity", "warning")
        command = "error" if severity == "error" else "warning" if severity == "warning" else "notice"
        title = f"Mapping as Code · {diagnostic.get('code', 'diagnostic')}"
        message = f"{diagnostic.get('path', '')}: {diagnostic.get('message', '')}"
        lines.append(
            f"::{command} file={_escape_property(file_path)},title={_escape_property(title)}::{_escape_data(message)}"
        )
    return lines
