import json

import yaml

from mapping_as_code.catalog_index import build_catalog_index, search_catalog
from mapping_as_code.cli import main
from mapping_as_code.performance import benchmark_mapping


def _mapping(mapping_id: str, title: str) -> dict:
    return {
        "schema_version": "0.1",
        "mapping": {
            "id": mapping_id,
            "title": title,
            "source": {"system": "legacy", "object": "customer"},
            "target": {"system": "s4hana", "object": "business-partner"},
            "fields": [
                {
                    "id": "customer-id",
                    "source": {"field": "customer_id"},
                    "target": {"field": "BusinessPartner"},
                    "transform": {"type": "copy"},
                    "business": {"owner": "master-data", "criticality": "high"},
                }
            ],
        },
    }


def test_catalog_index_and_search_are_deterministic(tmp_path):
    (tmp_path / "z.yaml").write_text(yaml.safe_dump(_mapping("customer", "Customer mapping")), encoding="utf-8")
    (tmp_path / "a.yaml").write_text(yaml.safe_dump(_mapping("supplier", "Supplier mapping")), encoding="utf-8")
    (tmp_path / "notes.yaml").write_text("status: draft\n", encoding="utf-8")

    first = build_catalog_index(tmp_path)
    second = build_catalog_index(tmp_path)

    assert first == second
    assert [item["mapping_id"] for item in first["mappings"]] == ["customer", "supplier"]
    assert search_catalog(first, "s4hana customer")[0]["mapping_id"] == "customer"


def test_catalog_cli_reports_duplicate_ids(tmp_path):
    (tmp_path / "one.yaml").write_text(yaml.safe_dump(_mapping("duplicate", "One")), encoding="utf-8")
    (tmp_path / "two.yaml").write_text(yaml.safe_dump(_mapping("duplicate", "Two")), encoding="utf-8")
    output = tmp_path / "index.json"

    assert main(["catalog-index", str(tmp_path), "--fail-on-duplicates", "--output", str(output)]) == 1
    result = json.loads(output.read_text(encoding="utf-8"))
    assert result["duplicates"] == [{"mapping_id": "duplicate", "paths": ["one.yaml", "two.yaml"]}]


def test_benchmark_exercises_validation_lineage_and_quality(tmp_path):
    result = benchmark_mapping(250)

    assert result["passed"] is True
    assert result["field_mappings"] == 250
    assert result["diagnostics"]["errors"] == 0
    assert result["lineage"]["edges"] == 250

    output = tmp_path / "benchmark.json"
    assert main(["benchmark", "--fields", "25", "--output", str(output)]) == 0
    assert json.loads(output.read_text(encoding="utf-8"))["passed"] is True
