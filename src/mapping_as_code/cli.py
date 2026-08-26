from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

from .adapters import (
    to_enterprise_change_graph,
    to_reconciliation,
    to_transformation_graph,
    to_visual_workbench,
)
from .annotations import github_annotations
from .artifacts import catalog_html, catalog_markdown, release_bundle, source_sha256, traceability_matrix
from .change_projection import to_enterprise_change_transition
from .core import diff_documents, lineage_graph, lineage_mermaid, mapping_summary, validate_document
from .governance import breaking_change_report, quality_scorecard, validation_report
from .graph_exports import lineage_cypher, lineage_graphml
from .interface_binding import bind_interface_contract
from .io import load_document
from .review import review_markdown, review_report
from .tabular import import_tabular


def _dump(value: Any) -> None:
    print(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False))


def _serialize(value: Any, format_name: str) -> str:
    if format_name == "json":
        return json.dumps(value, indent=2, sort_keys=False, ensure_ascii=False) + "\n"
    yaml_text = yaml.safe_dump(value, sort_keys=False, allow_unicode=True)
    if format_name == "markdown":
        return f"---\n{yaml_text}---\n"
    return yaml_text


def _write(text: str, output: str | None) -> None:
    if output:
        Path(output).write_text(text, encoding="utf-8")
        print(output)
    else:
        print(text, end="")


def _load_policy(path: str | None) -> dict[str, Any] | None:
    return load_document(path) if path else None


def _validate(args: argparse.Namespace) -> int:
    document = load_document(args.file)
    diagnostics = validate_document(document)
    payload = {
        "summary": mapping_summary(document),
        "diagnostics": [item.as_dict() for item in diagnostics],
        "valid": not any(item.severity == "error" for item in diagnostics),
    }
    if args.format == "json":
        _dump(payload)
    else:
        summary = payload["summary"]
        print(
            f'{summary["mapping_id"]}: {summary["field_mappings"]} mappings, '
            f'{summary["coverage"]:.0%} required-target coverage'
        )
        if diagnostics:
            for item in diagnostics:
                print(f"{item.severity.upper():7} {item.code}: {item.message} [{item.path}]")
        else:
            print("OK: no diagnostics")
    return 0 if payload["valid"] else 1


def _diff(args: argparse.Namespace) -> int:
    result = diff_documents(load_document(args.old), load_document(args.new))
    if args.format == "json":
        _dump(result)
    else:
        print(f'added: {", ".join(result["added"]) or "-"}')
        print(f'removed: {", ".join(result["removed"]) or "-"}')
        if result["changed"]:
            print("changed:")
            for item in result["changed"]:
                print(f'  - {item["id"]}: {", ".join(sorted(item["changes"]))}')
        else:
            print("changed: -")
    return 0


def _lineage(args: argparse.Namespace) -> int:
    document = load_document(args.file)
    if args.format == "mermaid":
        text = lineage_mermaid(document)
    elif args.format == "graphml":
        text = lineage_graphml(document)
    elif args.format == "cypher":
        text = lineage_cypher(document)
    else:
        text = json.dumps(lineage_graph(document), indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    _write(text, args.output)
    return 0


def _import(args: argparse.Namespace) -> int:
    document = import_tabular(args.file, value_maps_path=args.value_maps)
    _write(_serialize(document, args.format), args.output)
    return 0


def _score(args: argparse.Namespace) -> int:
    result = quality_scorecard(load_document(args.file))
    if args.format == "json":
        _dump(result)
    else:
        print(f'{result["score"]:.2f}/{result["maximum"]:.0f}')
        for name, value in result["dimensions"].items():
            print(f"{name}: {value:.2f}")
    return 0


def _report(args: argparse.Namespace) -> int:
    result = validation_report(load_document(args.file), _load_policy(args.policy))
    _write(_serialize(result, args.format), args.output)
    return 0 if result["valid"] else 1


def _annotations(args: argparse.Namespace) -> int:
    document = load_document(args.file)
    policy = _load_policy(args.policy)
    for line in github_annotations(document, file_path=args.annotation_file or args.file, policy=policy):
        print(line)
    return 0 if validation_report(document, policy)["valid"] else 1


def _gate(args: argparse.Namespace) -> int:
    result = breaking_change_report(
        load_document(args.old),
        load_document(args.new),
        _load_policy(args.policy),
    )
    _write(_serialize(result, args.format), args.output)
    return 0 if result["passed"] else 1


def _review(args: argparse.Namespace) -> int:
    result = review_report(
        load_document(args.old),
        load_document(args.new),
        _load_policy(args.policy),
    )
    if args.format == "markdown":
        _write(review_markdown(result), args.output)
    else:
        _write(_serialize(result, args.format), args.output)
    return 0 if result["passed"] else 1


def _traceability(args: argparse.Namespace) -> int:
    document = load_document(args.file)
    result = {"mapping_id": mapping_summary(document).get("mapping_id"), "rows": traceability_matrix(document)}
    _write(_serialize(result, args.format), args.output)
    return 0


def _catalog(args: argparse.Namespace) -> int:
    document = load_document(args.file)
    policy = _load_policy(args.policy)
    text = catalog_html(document, policy) if args.format == "html" else catalog_markdown(document, policy)
    _write(text, args.output)
    return 0


def _bundle(args: argparse.Namespace) -> int:
    document = load_document(args.file)
    result = release_bundle(
        document,
        source_name=Path(args.file).name,
        source_hash=source_sha256(args.file),
        policy=_load_policy(args.policy),
    )
    _write(_serialize(result, args.format), args.output)
    return 0 if result["validation"]["valid"] else 1


def _bind_interface(args: argparse.Namespace) -> int:
    result = bind_interface_contract(
        load_document(args.interface_file),
        load_document(args.mapping_file),
        mapping_uri=args.mapping_uri,
        revision=args.revision,
        allow_endpoint_mismatch=args.allow_endpoint_mismatch,
    )
    _write(_serialize(result, args.format), args.output)
    return 0


def _change_graph(args: argparse.Namespace) -> int:
    result = to_enterprise_change_transition(
        load_document(args.old),
        load_document(args.new),
        change_id=args.change_id,
    )
    _write(_serialize(result, args.format), args.output)
    return 0


def _project(args: argparse.Namespace) -> int:
    document = load_document(args.file)
    if args.target == "transformation-graph":
        result = to_transformation_graph(document)
    elif args.target == "enterprise-change-graph":
        result = to_enterprise_change_graph(document)
    elif args.target == "visual-workbench":
        result = to_visual_workbench(document)
    elif args.target == "reconciliation-as-code":
        missing = [
            name
            for name, value in (
                ("--source-file", args.source_file),
                ("--target-file", args.target_file),
                ("--source-key", args.source_key),
                ("--target-key", args.target_key),
            )
            if not value
        ]
        if missing:
            raise ValueError("reconciliation-as-code projection requires " + ", ".join(missing))
        result = to_reconciliation(
            document,
            source_file=args.source_file,
            target_file=args.target_file,
            source_key=args.source_key,
            target_key=args.target_key,
        )
    else:
        raise ValueError(f"unsupported projection target: {args.target}")
    _write(_serialize(result, args.format), args.output)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="map-code", description="Compile and govern enterprise mappings.")
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate", help="Validate one mapping specification")
    validate.add_argument("file")
    validate.add_argument("--format", choices=("text", "json"), default="text")
    validate.set_defaults(func=_validate)

    diff = sub.add_parser("diff", help="Compare two mapping versions")
    diff.add_argument("old")
    diff.add_argument("new")
    diff.add_argument("--format", choices=("text", "json"), default="text")
    diff.set_defaults(func=_diff)

    lineage = sub.add_parser("lineage", help="Build or export field-level lineage")
    lineage.add_argument("file")
    lineage.add_argument("--format", choices=("json", "mermaid", "graphml", "cypher"), default="json")
    lineage.add_argument("--output", "-o")
    lineage.set_defaults(func=_lineage)

    importer = sub.add_parser("import", help="Convert CSV/XLSX mapping workbooks to canonical Mapping as Code")
    importer.add_argument("file")
    importer.add_argument("--value-maps", help="Optional CSV with map,source,target columns")
    importer.add_argument("--format", choices=("yaml", "json"), default="yaml")
    importer.add_argument("--output", "-o")
    importer.set_defaults(func=_import)

    score = sub.add_parser("score", help="Calculate a transparent mapping quality score")
    score.add_argument("file")
    score.add_argument("--format", choices=("text", "json"), default="text")
    score.set_defaults(func=_score)

    report = sub.add_parser("report", help="Generate a policy-aware machine-readable validation report")
    report.add_argument("file")
    report.add_argument("--policy")
    report.add_argument("--format", choices=("yaml", "json"), default="json")
    report.add_argument("--output", "-o")
    report.set_defaults(func=_report)

    annotations = sub.add_parser("annotations", help="Emit GitHub workflow annotations for governance diagnostics")
    annotations.add_argument("file")
    annotations.add_argument("--policy")
    annotations.add_argument("--annotation-file", help="File label used in GitHub annotations; defaults to the mapping path")
    annotations.set_defaults(func=_annotations)

    gate = sub.add_parser("gate", help="Fail when a mapping revision violates breaking-change policy")
    gate.add_argument("old")
    gate.add_argument("new")
    gate.add_argument("--policy")
    gate.add_argument("--format", choices=("yaml", "json"), default="json")
    gate.add_argument("--output", "-o")
    gate.set_defaults(func=_gate)

    review = sub.add_parser("review", help="Generate one PR-oriented validation and semantic-change review")
    review.add_argument("old")
    review.add_argument("new")
    review.add_argument("--policy")
    review.add_argument("--format", choices=("yaml", "json", "markdown"), default="json")
    review.add_argument("--output", "-o")
    review.set_defaults(func=_review)

    traceability = sub.add_parser("traceability", help="Generate a field-level traceability matrix")
    traceability.add_argument("file")
    traceability.add_argument("--format", choices=("yaml", "json"), default="json")
    traceability.add_argument("--output", "-o")
    traceability.set_defaults(func=_traceability)

    catalog = sub.add_parser("catalog", help="Generate a human-readable mapping catalog")
    catalog.add_argument("file")
    catalog.add_argument("--policy")
    catalog.add_argument("--format", choices=("markdown", "html"), default="markdown")
    catalog.add_argument("--output", "-o")
    catalog.set_defaults(func=_catalog)

    bundle = sub.add_parser("bundle", help="Build an auditable mapping release bundle")
    bundle.add_argument("file")
    bundle.add_argument("--policy")
    bundle.add_argument("--format", choices=("yaml", "json"), default="json")
    bundle.add_argument("--output", "-o")
    bundle.set_defaults(func=_bundle)

    bind_interface = sub.add_parser("bind-interface", help="Bind a mapping artifact to an existing Interface as Code v1.0 contract")
    bind_interface.add_argument("interface_file")
    bind_interface.add_argument("mapping_file")
    bind_interface.add_argument("--mapping-uri", required=True)
    bind_interface.add_argument("--revision")
    bind_interface.add_argument("--allow-endpoint-mismatch", action="store_true")
    bind_interface.add_argument("--format", choices=("yaml", "json"), default="yaml")
    bind_interface.add_argument("--output", "-o")
    bind_interface.set_defaults(func=_bind_interface)

    change_graph = sub.add_parser("change-graph", help="Project a mapping revision as Enterprise Change Graph impact seeds")
    change_graph.add_argument("old")
    change_graph.add_argument("new")
    change_graph.add_argument("--change-id")
    change_graph.add_argument("--format", choices=("yaml", "json"), default="json")
    change_graph.add_argument("--output", "-o")
    change_graph.set_defaults(func=_change_graph)

    project = sub.add_parser("project", help="Project a mapping into an adjacent enterprise-as-code contract")
    project.add_argument("file")
    project.add_argument(
        "--target",
        required=True,
        choices=(
            "transformation-graph",
            "reconciliation-as-code",
            "enterprise-change-graph",
            "visual-workbench",
        ),
    )
    project.add_argument("--format", choices=("yaml", "json", "markdown"), default="json")
    project.add_argument("--output", "-o")
    project.add_argument("--source-file")
    project.add_argument("--target-file")
    project.add_argument("--source-key")
    project.add_argument("--target-key")
    project.set_defaults(func=_project)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"map-code: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
