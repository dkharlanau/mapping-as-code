from __future__ import annotations

from typing import Any


def _cell(value: Any) -> str:
    if value is None:
        return ""
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_markdown(document: dict[str, Any]) -> str:
    metadata = document.get("metadata", {})
    source = document.get("source", {})
    target = document.get("target", {})
    title = metadata.get("name", "Mapping specification")
    lines = [
        f"# {title}", "", metadata.get("description", "Generated from a Mapping as Code specification."), "",
        "## Scope", "", f"- Version: `{metadata.get('version', 'n/a')}`",
        f"- Source: `{source.get('system', '?')}` / `{source.get('object', '?')}`",
        f"- Target: `{target.get('system', '?')}` / `{target.get('object', '?')}`",
        f"- Field mappings: **{len(document.get('fields', []))}**", "", "## Field mappings", "",
        "| ID | Source | Target | Transform | Required | Description |", "|---|---|---|---|---|---|",
    ]
    for field in document.get("fields", []):
        transform = field.get("transform", {"type": "copy"})
        transform_text = transform.get("type", "copy")
        if transform_text == "lookup":
            transform_text += f" ({transform.get('reference', '?')})"
        elif transform_text == "constant":
            transform_text += f" = {transform.get('value', '')}"
        lines.append("| " + " | ".join([
            _cell(field.get("id")), _cell(field.get("source", {}).get("path")), _cell(field.get("target", {}).get("path")),
            _cell(transform_text), "yes" if field.get("constraints", {}).get("required") else "no", _cell(field.get("description")),
        ]) + " |")
    value_maps = document.get("valueMaps", {})
    if value_maps:
        lines.extend(["", "## Value maps"])
        for name, entries in value_maps.items():
            lines.extend(["", f"### {name}", "", "| From | To |", "|---|---|"])
            for entry in entries:
                lines.append(f"| {_cell(entry.get('from'))} | {_cell(entry.get('to'))} |")
    return "\n".join(lines) + "\n"
