from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

import yaml

from .adapters import to_reconciliation
from .artifacts import source_sha256
from .core import mapping_summary
from .governance import quality_scorecard, validation_report
from .io import load_document
from .review import review_markdown, review_report
from .tabular import import_tabular


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=False, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_yaml(path: Path, value: Any) -> None:
    path.write_text(yaml.safe_dump(value, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _rac_config(args: argparse.Namespace) -> dict[str, str] | None:
    values = {
        "source_file": args.source_file,
        "target_file": args.target_file,
        "source_key": args.source_key,
        "target_key": args.target_key,
    }
    if not any(values.values()):
        return None
    missing = [name.replace("_", "-") for name, value in values.items() if not value]
    if missing:
        raise ValueError("RAC handoff requires --" + ", --".join(missing))
    return {name: str(value) for name, value in values.items()}


def _safe_output_dir(path: str, *, force: bool) -> Path:
    output_dir = Path(path).expanduser().resolve()
    expected = [
        "mapping.yaml",
        "validation-report.json",
        "quality-score.json",
        "preflight-summary.json",
        "semantic-review.json",
        "semantic-review.md",
        "reconciliation.yaml",
    ]
    existing = [output_dir / name for name in expected if (output_dir / name).exists()]
    if existing and not force:
        joined = ", ".join(str(path) for path in existing)
        raise ValueError(f"preflight output already exists: {joined}; use --force to overwrite")
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def _relative_runtime_path(path: str, output_dir: Path) -> str:
    return os.path.relpath(Path(path).expanduser().resolve(), output_dir)


def run_preflight(args: argparse.Namespace) -> int:
    output_dir = _safe_output_dir(args.output_dir, force=args.force)
    document = import_tabular(args.workbook, value_maps_path=args.value_maps)
    policy = load_document(args.policy) if args.policy else None

    mapping_path = output_dir / "mapping.yaml"
    _write_yaml(mapping_path, document)

    validation = validation_report(document, policy)
    quality = quality_scorecard(document)
    _write_json(output_dir / "validation-report.json", validation)
    _write_json(output_dir / "quality-score.json", quality)

    review = None
    if args.baseline:
        review = review_report(load_document(args.baseline), document, policy)
        _write_json(output_dir / "semantic-review.json", review)
        (output_dir / "semantic-review.md").write_text(
            review_markdown(review, max_items=args.max_review_items),
            encoding="utf-8",
        )

    rac = None
    config = _rac_config(args)
    if config is not None and validation["valid"]:
        rac = to_reconciliation(
            document,
            source_file=_relative_runtime_path(config["source_file"], output_dir),
            target_file=_relative_runtime_path(config["target_file"], output_dir),
            source_key=config["source_key"],
            target_key=config["target_key"],
            mapping_artifact_file="mapping.yaml",
            mapping_artifact_sha256=source_sha256(str(mapping_path)),
        )
        _write_yaml(output_dir / "reconciliation.yaml", rac)

    summary = {
        "workbook": str(Path(args.workbook).expanduser().resolve()),
        "mapping": mapping_summary(document),
        "validation": {
            "valid": bool(validation["valid"]),
            "diagnostics": len(validation.get("diagnostics", [])),
        },
        "quality": {
            "score": quality.get("score"),
            "maximum": quality.get("maximum"),
        },
        "semantic_review": None
        if review is None
        else {
            "passed": bool(review["passed"]),
            "baseline": str(Path(args.baseline).expanduser().resolve()),
        },
        "rac_handoff": {
            "requested": config is not None,
            "generated": rac is not None,
            "reason": None if rac is not None or config is None else "mapping validation failed",
        },
        "artifacts": {
            "mapping": str(mapping_path),
            "validation_report": str(output_dir / "validation-report.json"),
            "quality_score": str(output_dir / "quality-score.json"),
            "semantic_review": str(output_dir / "semantic-review.json") if review is not None else None,
            "reconciliation": str(output_dir / "reconciliation.yaml") if rac is not None else None,
        },
    }
    _write_json(output_dir / "preflight-summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False))

    if not validation["valid"]:
        return 1
    if review is not None and not review["passed"]:
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="map-code-preflight",
        description=(
            "Import a mapping workbook, preserve a canonical mapping contract, emit deterministic quality evidence, "
            "optionally review it against a baseline, and optionally generate a pinned Reconciliation as Code handoff."
        ),
    )
    parser.add_argument("workbook", help="CSV/XLSX/XLSM mapping workbook to import.")
    parser.add_argument("--value-maps", help="Optional CSV value-map file when value maps are not embedded in XLSX.")
    parser.add_argument("--policy", help="Optional Mapping as Code governance policy.")
    parser.add_argument("--baseline", help="Optional canonical Mapping as Code YAML/JSON baseline for semantic review.")
    parser.add_argument("--output-dir", default="build/mapping-preflight", help="Directory for canonical and evidence artifacts.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing preflight artifacts in the output directory.")
    parser.add_argument("--max-review-items", type=int, default=20, help="Maximum semantic-review items rendered to Markdown.")
    parser.add_argument("--source-file", help="Optional source data extract for RAC handoff.")
    parser.add_argument("--target-file", help="Optional target data extract for RAC handoff.")
    parser.add_argument("--source-key", help="Explicit source business key for RAC handoff.")
    parser.add_argument("--target-key", help="Explicit target business key for RAC handoff.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return run_preflight(args)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"map-code-preflight: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
