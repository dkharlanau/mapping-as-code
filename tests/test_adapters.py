import re

from mapping_as_code.adapters import (
    to_enterprise_change_graph,
    to_reconciliation,
    to_transformation_graph,
    to_visual_workbench,
)


def sample():
    return {
        "schema_version": "0.1",
        "mapping": {
            "id": "legacy-customer-to-s4-business-partner",
            "title": "Customer mapping",
            "source": {"system": "legacy-erp", "object": "customer"},
            "target": {"system": "s4hana", "object": "business-partner"},
            "fields": [
                {
                    "id": "customer-id",
                    "source": {"field": "customer_id"},
                    "target": {"field": "BusinessPartner"},
                    "transform": {"type": "copy"},
                    "business": {"criticality": "high"},
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
        "value_maps": {"countries": {"DE": "DE", "US": "US"}},
    }


def test_transformation_graph_projection_matches_contract_shape():
    result = to_transformation_graph(sample())
    assert result["version"] == "0.1"
    assert result["project"]["id"] == "legacy-customer-to-s4-business-partner"
    assert result["nodes"] and result["edges"]
    allowed = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
    assert all(allowed.match(node["id"]) for node in result["nodes"])
    assert any(node["type"] == "mapping" for node in result["nodes"])
    assert any(edge["type"] == "maps_to" for edge in result["edges"])


def test_enterprise_change_graph_projection_preserves_provenance_and_criticality():
    result = to_enterprise_change_graph(sample())
    assert result["version"] == 1
    assert result["metadata"]["source"] == "mapping-as-code"
    assert all(node["provenance"] == "mapping-as-code" for node in result["nodes"])
    assert any(node.get("criticality") == "high" for node in result["nodes"])
    assert all(edge["propagation"] == "forward" for edge in result["edges"])


def test_visual_workbench_projection_builds_three_business_lanes():
    result = to_visual_workbench(sample())["visual"]
    assert result["kind"] == "data-flow"
    assert [group["id"] for group in result["groups"]] == ["source", "mapping", "target"]
    assert any(node["type"] == "step" for node in result["nodes"])
    assert any(node.get("status") == "warning" for node in result["nodes"])
    visual_id = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]*$")
    assert all(visual_id.match(node["id"]) for node in result["nodes"])


def test_reconciliation_projection_only_generates_safe_field_checks():
    result = to_reconciliation(
        sample(),
        source_file="legacy.csv",
        target_file="s4.csv",
        source_key="customer_id",
        target_key="BusinessPartner",
    )
    assert result["version"] == 1
    assert result["source"]["format"] == "csv"
    assert result["target"]["format"] == "csv"
    checks = {check["id"]: check for check in result["checks"]}
    assert checks["customer-id"]["type"] == "field_match"
    assert checks["country"]["map"] == {"DE": "DE", "US": "US"}
    assert result["generated_from"]["projection_mode"] == "detached_snapshot"
    assert "mapping_artifacts" not in result
    assert "category" not in checks
    assert result["materiality"]["fields"]["BusinessPartner"]["critical"] is True


def test_reconciliation_projection_can_link_authoritative_mapping_artifact():
    digest = "a" * 64
    result = to_reconciliation(
        sample(),
        source_file="legacy.csv",
        target_file="s4.csv",
        source_key="customer_id",
        target_key="BusinessPartner",
        mapping_artifact_file="mapping.yaml",
        mapping_artifact_sha256=digest,
    )
    checks = {check["id"]: check for check in result["checks"]}
    assert checks["country"]["map_ref"] == {"artifact": "mapping-source", "field": "country"}
    assert "map" not in checks["country"]
    assert result["mapping_artifacts"]["mapping-source"] == {"file": "mapping.yaml", "sha256": digest}
    assert result["generated_from"]["projection_mode"] == "linked_source"


def test_reconciliation_supports_composite_keys():
    result = to_reconciliation(
        sample(),
        source_file="legacy.parquet",
        target_file="s4.parquet",
        source_key="company,customer_id",
        target_key="CompanyCode,BusinessPartner",
    )
    assert result["source"]["key"] == ["company", "customer_id"]
    assert result["target"]["key"] == ["CompanyCode", "BusinessPartner"]
