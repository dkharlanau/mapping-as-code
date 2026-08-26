from pathlib import Path

import pytest
import yaml

from mapping_as_code.composition import CompositionError, compose_manifest
from mapping_as_code.core import validate_document


def test_example_composition_namespaces_ids_maps_and_required_fields():
    document, report = compose_manifest("examples/composition/customer.composition.yaml")
    ids = [item["id"] for item in document["mapping"]["fields"]]
    assert ids == ["customer-id", "geo:country", "address:city"]
    country = next(item for item in document["mapping"]["fields"] if item["id"] == "geo:country")
    assert country["transform"]["reference"] == "geo:iso-country"
    assert document["value_maps"]["geo:iso-country"]["USA"] == "US"
    assert document["mapping"]["source"]["required_fields"] == ["customer_id", "country", "city"]
    assert document["mapping"]["target"]["required_fields"] == ["BusinessPartner", "Country", "CityName"]
    assert not [item for item in validate_document(document) if item.severity == "error"]
    assert report["result"]["field_mappings"] == 3
    assert report["fragments"][0]["namespace"] == "geo"


def test_composition_is_deterministic():
    first_document, first_report = compose_manifest("examples/composition/customer.composition.yaml")
    second_document, second_report = compose_manifest("examples/composition/customer.composition.yaml")
    assert first_document == second_document
    assert first_report["result"]["canonical_sha256"] == second_report["result"]["canonical_sha256"]


def _write_yaml(path: Path, value):
    path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")


def _base():
    return {
        "schema_version": "0.1",
        "mapping": {
            "id": "compose-test",
            "source": {"system": "a", "object": "x"},
            "target": {"system": "b", "object": "y"},
            "fields": [
                {
                    "id": "base",
                    "source": {"field": "A"},
                    "target": {"field": "B"},
                    "transform": {"type": "copy"},
                }
            ],
        },
    }


def test_composition_rejects_fragment_path_traversal(tmp_path: Path):
    root = tmp_path / "project"
    root.mkdir()
    _write_yaml(root / "base.yaml", _base())
    _write_yaml(tmp_path / "outside.yaml", {"fragment_version": 1, "fields": [{"id": "x", "target": {"field": "X"}}]})
    _write_yaml(
        root / "composition.yaml",
        {"composition_version": 1, "base": "base.yaml", "fragments": [{"path": "../outside.yaml"}]},
    )
    with pytest.raises(CompositionError, match="escapes the composition directory"):
        compose_manifest(root / "composition.yaml")


def test_composition_rejects_duplicate_ids_without_namespace(tmp_path: Path):
    _write_yaml(tmp_path / "base.yaml", _base())
    fragment = {"fragment_version": 1, "fields": [{"id": "same", "source": {"field": "C"}, "target": {"field": "D"}}]}
    _write_yaml(tmp_path / "one.yaml", fragment)
    _write_yaml(tmp_path / "two.yaml", fragment)
    _write_yaml(
        tmp_path / "composition.yaml",
        {
            "composition_version": 1,
            "base": "base.yaml",
            "fragments": [{"path": "one.yaml"}, {"path": "two.yaml"}],
        },
    )
    with pytest.raises(CompositionError, match="duplicate field mapping id"):
        compose_manifest(tmp_path / "composition.yaml")


def test_namespace_only_rewrites_lookup_references_to_local_maps(tmp_path: Path):
    _write_yaml(tmp_path / "base.yaml", {**_base(), "value_maps": {"global-map": {"x": "y"}}})
    fragment = {
        "fragment_version": 1,
        "fields": [
            {"id": "local", "source": {"field": "L"}, "target": {"field": "L2"}, "transform": {"type": "lookup", "reference": "local-map"}},
            {"id": "external", "source": {"field": "E"}, "target": {"field": "E2"}, "transform": {"type": "lookup", "reference": "global-map"}},
        ],
        "value_maps": {"local-map": {"a": "b"}},
    }
    _write_yaml(tmp_path / "fragment.yaml", fragment)
    _write_yaml(
        tmp_path / "composition.yaml",
        {"composition_version": 1, "base": "base.yaml", "fragments": [{"path": "fragment.yaml", "namespace": "shared"}]},
    )
    document, _ = compose_manifest(tmp_path / "composition.yaml")
    fields = {item["id"]: item for item in document["mapping"]["fields"]}
    assert fields["shared:local"]["transform"]["reference"] == "shared:local-map"
    assert fields["shared:external"]["transform"]["reference"] == "global-map"
