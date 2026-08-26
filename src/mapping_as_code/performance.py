from __future__ import annotations

import time
from typing import Any

from .core import lineage_graph, validate_document
from .governance import quality_scorecard


def synthetic_mapping(field_count: int) -> dict[str, Any]:
    if field_count < 1:
        raise ValueError("field_count must be at least 1")
    fields: list[dict[str, Any]] = []
    source_required: list[str] = []
    target_required: list[str] = []
    width = max(4, len(str(field_count)))
    for index in range(field_count):
        suffix = f"{index:0{width}d}"
        source_field = f"SRC_{suffix}"
        target_field = f"TGT_{suffix}"
        source_required.append(source_field)
        target_required.append(target_field)
        fields.append(
            {
                "id": f"field-{suffix}",
                "source": {"field": source_field},
                "target": {"field": target_field},
                "transform": {"type": "copy"},
                "rules": {"required": True},
                "business": {
                    "owner": "benchmark-owner",
                    "criticality": "medium",
                    "rationale": "Synthetic benchmark mapping rule.",
                },
            }
        )
    return {
        "schema_version": "0.1",
        "mapping": {
            "id": f"synthetic-{field_count}-field-mapping",
            "title": f"Synthetic {field_count} field mapping",
            "source": {
                "system": "synthetic-source",
                "object": "record",
                "required_fields": source_required,
            },
            "target": {
                "system": "synthetic-target",
                "object": "record",
                "required_fields": target_required,
            },
            "fields": fields,
        },
    }


def benchmark_mapping(field_count: int, *, max_seconds: float | None = None) -> dict[str, Any]:
    document = synthetic_mapping(field_count)

    start = time.perf_counter()
    diagnostics = validate_document(document)
    validation_seconds = time.perf_counter() - start

    start = time.perf_counter()
    lineage = lineage_graph(document)
    lineage_seconds = time.perf_counter() - start

    start = time.perf_counter()
    quality = quality_scorecard(document)
    quality_seconds = time.perf_counter() - start

    total_seconds = validation_seconds + lineage_seconds + quality_seconds
    errors = [item for item in diagnostics if item.severity == "error"]
    threshold_passed = max_seconds is None or total_seconds <= max_seconds
    passed = not errors and len(lineage["edges"]) == field_count and threshold_passed
    return {
        "benchmark_version": 1,
        "field_mappings": field_count,
        "timings_seconds": {
            "validation": round(validation_seconds, 6),
            "lineage": round(lineage_seconds, 6),
            "quality": round(quality_seconds, 6),
            "total": round(total_seconds, 6),
        },
        "diagnostics": {
            "total": len(diagnostics),
            "errors": len(errors),
        },
        "lineage": {
            "nodes": len(lineage["nodes"]),
            "edges": len(lineage["edges"]),
        },
        "quality_score": quality["score"],
        "threshold": {"max_seconds": max_seconds, "passed": threshold_passed},
        "passed": passed,
    }
