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
from .core import diff_documents, lineage_graph, lineage_mermaid, mapping_summary, validate_document
from .io import load_document
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
        print(lineage_mermaid(document), end="")
    else:
        _dump(lineage_graph(document))
    return 0


def _import(args: argparse.Namespace) -> int:
    document = import_tabular(args.file, value_maps_path=args.value_maps)
    _write(_serialize(document, args.format), args.output)
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

    lineage = sub.add_parser("lineage", help="Build field-level lineage")
    lineage.add_argument("file")
    lineage.add_argument("--format", choices=("json", "mermaid"), default="json")
    lineage.set_defaults(func=_lineage)

    importer = sub.add_parser("import", help="Convert CSV/XLSX mapping workbooks to canonical Mapping as Code")
    importer.add_argument("file")
    importer.add_argument("--value-maps", help="Optional CSV with map,source,target columns")
    importer.add_argument("--format", choices=("yaml", "json"), default="yaml")
    importer.add_argument("--output", "-o")
    importer.set_defaults(func=_import)

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
