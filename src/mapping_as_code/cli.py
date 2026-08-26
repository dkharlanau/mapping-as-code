from __future__ import annotations

import argparse
import json
from pathlib import Path

from .diff import diff_documents
from .docs import render_markdown
from .importers import import_tabular
from .io import dump_yaml, load_document
from .validation import validate_document


def cmd_validate(args: argparse.Namespace) -> int:
    failed = False
    for filename in args.files:
        document = load_document(filename)
        findings = validate_document(document)
        if findings:
            failed = True
            print(f"{filename}: INVALID ({len(findings)} finding(s))")
            for finding in findings:
                print(f"  {finding}")
        else:
            print(f"{filename}: OK")
    return 1 if failed else 0


def cmd_diff(args: argparse.Namespace) -> int:
    result = diff_documents(load_document(args.before), load_document(args.after))
    print(json.dumps(result.as_dict(), indent=2, ensure_ascii=False))
    return 0


def cmd_docs(args: argparse.Namespace) -> int:
    output = render_markdown(load_document(args.file))
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(args.output)
    else:
        print(output, end="")
    return 0


def cmd_import(args: argparse.Namespace) -> int:
    document = import_tabular(args.file, name=args.name, source_system=args.source_system, source_object=args.source_object, target_system=args.target_system, target_object=args.target_object)
    output = dump_yaml(document)
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(args.output)
    else:
        print(output, end="")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mapcode", description="Mapping as Code CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate_parser = subparsers.add_parser("validate", help="validate mapping specifications")
    validate_parser.add_argument("files", nargs="+")
    validate_parser.set_defaults(func=cmd_validate)
    diff_parser = subparsers.add_parser("diff", help="compare two mapping specification versions")
    diff_parser.add_argument("before")
    diff_parser.add_argument("after")
    diff_parser.set_defaults(func=cmd_diff)
    docs_parser = subparsers.add_parser("docs", help="generate Markdown documentation")
    docs_parser.add_argument("file")
    docs_parser.add_argument("-o", "--output")
    docs_parser.set_defaults(func=cmd_docs)
    import_parser = subparsers.add_parser("import", help="import CSV or XLSX mapping tables")
    import_parser.add_argument("file")
    import_parser.add_argument("--name", required=True)
    import_parser.add_argument("--source-system", required=True)
    import_parser.add_argument("--source-object", required=True)
    import_parser.add_argument("--target-system", required=True)
    import_parser.add_argument("--target-object", required=True)
    import_parser.add_argument("-o", "--output")
    import_parser.set_defaults(func=cmd_import)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
