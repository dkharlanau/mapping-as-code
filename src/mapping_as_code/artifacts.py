from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path
from typing import Any

from .core import lineage_graph, mapping_summary
from .governance import canonical_hash, validation_report


def source_sha256(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def traceability_matrix(document: dict[str, Any]) -> list[dict[str, Any]]:
    mapping = document.get("mapping") if isinstance(document.get("mapping"), dict) else {}
    source = mapping.get("source") if isinstance(mapping.get("source"), dict) else {}
    target = mapping.get("target") if isinstance(mapping.get("target"), dict) else {}
    fields = mapping.get("fields") if isinstance(mapping.get("fields"), list) else []
    rows: list[dict[str, Any]] = []
    for index, item in enumerate(fields):
        if not isinstance(item, dict):
            continue
        source_ep = item.get("source") if isinstance(item.get("source"), dict) else {}
        target_ep = item.get("target") if isinstance(item.get("target"), dict) else {}
        transform = item.get("transform") if isinstance(item.get("transform"), dict) else {"type": "copy"}
        rules = item.get("rules") if isinstance(item.get("rules"), dict) else {}
        business = item.get("business") if isinstance(item.get("business"), dict) else {}
        source_field = source_ep.get("field")
        target_field = target_ep.get("field")
        rows.append(
            {
                "id": item.get("id", f"field-{index}"),
                "source": (
                    f"{source.get('system')}.{source.get('object')}.{source_field}" if source_field else None
                ),
                "target": (
                    f"{target.get('system')}.{target.get('object')}.{target_field}" if target_field else None
                ),
                "transform": transform.get("type", "copy"),
                "reference": transform.get("reference"),
                "required": bool(rules.get("required", False)),
                "owner": business.get("owner"),
                "criticality": business.get("criticality"),
                "rationale": business.get("rationale"),
            }
        )
    return rows


def catalog_markdown(document: dict[str, Any], policy: dict[str, Any] | None = None) -> str:
    mapping = document.get("mapping") if isinstance(document.get("mapping"), dict) else {}
    report = validation_report(document, policy)
    rows = traceability_matrix(document)
    source = mapping.get("source") if isinstance(mapping.get("source"), dict) else {}
    target = mapping.get("target") if isinstance(mapping.get("target"), dict) else {}
    lines = [
        f"# {mapping.get('title') or mapping.get('id') or 'Mapping'}",
        "",
        str(mapping.get("description") or "Generated Mapping as Code catalog."),
        "",
        "## Overview",
        "",
        f"- Mapping ID: `{mapping.get('id')}`",
        f"- Source: `{source.get('system')}.{source.get('object')}`",
        f"- Target: `{target.get('system')}.{target.get('object')}`",
        f"- Field mappings: **{len(rows)}**",
        f"- Required target coverage: **{report['summary']['coverage']:.0%}**",
        f"- Quality score: **{report['quality']['score']:.2f}/100**",
        f"- Governance result: **{'PASS' if report['valid'] else 'FAIL'}**",
        "",
        "## Traceability",
        "",
        "| ID | Source | Target | Transform | Required | Owner | Criticality |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {id} | {source} | {target} | {transform} | {required} | {owner} | {criticality} |".format(
                id=row["id"],
                source=row["source"] or "—",
                target=row["target"] or "—",
                transform=(f"{row['transform']} ({row['reference']})" if row["reference"] else row["transform"]),
                required="yes" if row["required"] else "no",
                owner=row["owner"] or "—",
                criticality=row["criticality"] or "—",
            )
        )
    lines.extend(["", "## Business rationale", ""])
    rationale_rows = [row for row in rows if row["rationale"]]
    if rationale_rows:
        for row in rationale_rows:
            lines.append(f"- **{row['id']}** — {row['rationale']}")
    else:
        lines.append("No field-level rationale is recorded.")

    lines.extend(["", "## Governance diagnostics", ""])
    if report["diagnostics"]:
        for item in report["diagnostics"]:
            lines.append(f"- **{item['severity'].upper()} · {item['code']}** — {item['message']} (`{item['path']}`)")
    else:
        lines.append("No diagnostics.")
    lines.extend(["", f"Canonical SHA-256: `{report['document_sha256']}`", ""])
    return "\n".join(lines)


def catalog_html(document: dict[str, Any], policy: dict[str, Any] | None = None) -> str:
    mapping = document.get("mapping") if isinstance(document.get("mapping"), dict) else {}
    report = validation_report(document, policy)
    rows = traceability_matrix(document)
    title = html.escape(str(mapping.get("title") or mapping.get("id") or "Mapping"))
    description = html.escape(str(mapping.get("description") or "Generated Mapping as Code catalog."))
    body_rows = "".join(
        "<tr>"
        f"<td><code>{html.escape(str(row['id']))}</code></td>"
        f"<td>{html.escape(str(row['source'] or '—'))}</td>"
        f"<td>{html.escape(str(row['target'] or '—'))}</td>"
        f"<td>{html.escape(str(row['transform']))}</td>"
        f"<td>{'yes' if row['required'] else 'no'}</td>"
        f"<td>{html.escape(str(row['owner'] or '—'))}</td>"
        f"<td>{html.escape(str(row['criticality'] or '—'))}</td>"
        "</tr>"
        for row in rows
    )
    diagnostics = "".join(
        f"<li><strong>{html.escape(item['severity'].upper())} · {html.escape(item['code'])}</strong> — "
        f"{html.escape(item['message'])} <code>{html.escape(item['path'])}</code></li>"
        for item in report["diagnostics"]
    ) or "<li>No diagnostics.</li>"
    status = "PASS" if report["valid"] else "FAIL"
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title><style>
body{{font-family:Inter,ui-sans-serif,system-ui,sans-serif;max-width:1180px;margin:48px auto;padding:0 24px;color:#171717;line-height:1.5}}
h1{{font-size:36px;letter-spacing:-.03em}} .metrics{{display:flex;gap:24px;flex-wrap:wrap;margin:28px 0}}
.metric{{border:1px solid #ddd;border-radius:10px;padding:14px 18px;min-width:150px}} .metric b{{display:block;font-size:24px}}
table{{border-collapse:collapse;width:100%;font-size:14px}} th,td{{text-align:left;border-bottom:1px solid #e5e5e5;padding:10px 8px;vertical-align:top}}
code{{font-family:ui-monospace,SFMono-Regular,monospace;font-size:.92em}} footer{{margin-top:36px;color:#666;font-size:13px}}
</style></head><body><h1>{title}</h1><p>{description}</p>
<div class="metrics"><div class="metric">Quality<b>{report['quality']['score']:.2f}</b>/ 100</div>
<div class="metric">Coverage<b>{report['summary']['coverage']:.0%}</b>required targets</div>
<div class="metric">Governance<b>{status}</b>policy {html.escape(report['policy']['name'])}</div></div>
<h2>Traceability</h2><table><thead><tr><th>ID</th><th>Source</th><th>Target</th><th>Transform</th><th>Required</th><th>Owner</th><th>Criticality</th></tr></thead><tbody>{body_rows}</tbody></table>
<h2>Diagnostics</h2><ul>{diagnostics}</ul><footer>Canonical SHA-256: <code>{report['document_sha256']}</code></footer></body></html>\n"""


def release_bundle(
    document: dict[str, Any],
    *,
    source_name: str,
    source_hash: str,
    policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    report = validation_report(document, policy)
    return {
        "bundle_version": 1,
        "mapping_id": mapping_summary(document).get("mapping_id"),
        "source": {"name": source_name, "sha256": source_hash},
        "canonical_sha256": canonical_hash(document),
        "validation": report,
        "traceability": traceability_matrix(document),
        "lineage": lineage_graph(document),
    }


def bundle_json(bundle: dict[str, Any]) -> str:
    return json.dumps(bundle, ensure_ascii=False, indent=2, sort_keys=False) + "\n"
