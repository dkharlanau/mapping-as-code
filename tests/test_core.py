from copy import deepcopy

from mapping_as_code.core import diff_documents, lineage_graph, mapping_summary, validate_document


def sample():
    return {
        "schema_version": "0.1",
        "mapping": {
            "id": "customer",
            "source": {"system": "legacy", "object": "customer", "required_fields": ["id", "country"]},
            "target": {
                "system": "s4",
                "object": "bp",
                "required_fields": ["BusinessPartner", "Country", "Category"],
            },
            "fields": [
                {
                    "id": "id",
                    "source": {"field": "id"},
                    "target": {"field": "BusinessPartner"},
                    "transform": {"type": "copy"},
                },
                {
                    "id": "country",
                    "source": {"field": "country"},
                    "target": {"field": "Country"},
                    "transform": {"type": "lookup", "reference": "countries"},
                },
                {
                    "id": "category",
                    "target": {"field": "Category"},
                    "transform": {"type": "constant", "value": "2"},
                },
            ],
        },
        "value_maps": {"countries": {"DE": "DE"}},
    }


def codes(document):
    return {item.code for item in validate_document(document)}


def test_valid_mapping_and_coverage():
    document = sample()
    assert validate_document(document) == []
    assert mapping_summary(document)["coverage"] == 1.0


def test_missing_required_target_is_error():
    document = sample()
    document["mapping"]["fields"].pop()
    assert "target.required.unmapped" in codes(document)


def test_unknown_lookup_is_error():
    document = sample()
    document["mapping"]["fields"][1]["transform"]["reference"] = "missing"
    assert "lookup.reference.unknown" in codes(document)


def test_duplicate_target_is_error():
    document = sample()
    duplicate = deepcopy(document["mapping"]["fields"][0])
    duplicate["id"] = "id-duplicate"
    document["mapping"]["fields"].append(duplicate)
    assert "target.duplicate" in codes(document)


def test_diff_reports_added_and_semantic_changes():
    old = sample()
    new = deepcopy(old)
    new["mapping"]["fields"][0]["rules"] = {"required": True}
    new["mapping"]["fields"].append(
        {
            "id": "city",
            "source": {"field": "city"},
            "target": {"field": "City"},
            "transform": {"type": "copy"},
        }
    )
    result = diff_documents(old, new)
    assert result["added"] == ["city"]
    assert result["changed"][0]["id"] == "id"
    assert "rules" in result["changed"][0]["changes"]


def test_lineage_contains_constant_and_field_edges():
    graph = lineage_graph(sample())
    assert len(graph["edges"]) == 3
    assert any(node["kind"] == "constant" for node in graph["nodes"])
    assert any(edge["transform"] == "lookup" for edge in graph["edges"])
