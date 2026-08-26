from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from .core import diff_documents, lineage_graph, lineage_mermaid, mapping_summary, validate_document
from .io import load_document


def _dump(value: Any) -> None:
    print(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False))


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
