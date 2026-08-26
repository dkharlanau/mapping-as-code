from mapping_as_code.artifacts import catalog_html, catalog_markdown, release_bundle, traceability_matrix
from mapping_as_code.io import load_document


def test_traceability_matrix_preserves_mapping_intent():
    document = load_document("examples/customer-master.yaml")
    rows = traceability_matrix(document)
    assert len(rows) == 4
    country = next(row for row in rows if row["id"] == "customer-country")
    assert country["source"] == "legacy-erp.customer.country"
    assert country["target"] == "s4hana.business-partner.Country"
    assert country["transform"] == "lookup"
    assert country["reference"] == "iso-country"


def test_markdown_catalog_contains_score_and_traceability():
    document = load_document("examples/customer-master.yaml")
    text = catalog_markdown(document)
    assert "## Traceability" in text
    assert "Quality score" in text
    assert "customer-country" in text
    assert "Canonical SHA-256" in text


def test_html_catalog_is_standalone_and_escaped():
    document = load_document("examples/customer-master.yaml")
    document["mapping"]["title"] = "Customer <Mapping>"
    text = catalog_html(document)
    assert text.startswith("<!doctype html>")
    assert "Customer &lt;Mapping&gt;" in text
    assert "<table>" in text


def test_release_bundle_contains_source_validation_traceability_and_lineage():
    document = load_document("examples/customer-master.yaml")
    bundle = release_bundle(document, source_name="customer-master.yaml", source_hash="a" * 64)
    assert bundle["bundle_version"] == 1
    assert bundle["source"]["sha256"] == "a" * 64
    assert bundle["validation"]["mapping_id"] == "legacy-customer-to-s4-business-partner"
    assert len(bundle["traceability"]) == 4
    assert bundle["lineage"]["edges"]
