from copy import deepcopy

import pytest

from mapping_as_code.io import load_document
from mapping_as_code.review import review_markdown, review_report


def test_review_combines_current_validation_change_gate_and_quality_delta():
    old = load_document("examples/customer-master.yaml")
    new = load_document("examples/customer-master-v2.yaml")
    report = review_report(old, new, load_document("policies/enterprise-strict.yaml"))
    assert report["review_version"] == 1
    assert report["changes"]["breaking"] is True
    assert "score" in report["quality_delta"]
    assert report["passed"] is False


def test_review_markdown_is_pr_readable():
    old = load_document("examples/customer-master.yaml")
    new = load_document("examples/customer-master-v2.yaml")
    report = review_report(old, new, load_document("policies/migration-pragmatic.yaml"))
    text = review_markdown(report)
    assert text.startswith("## Mapping as Code review")
    assert "| Quality |" in text
    assert "### Change events" in text
    assert "Baseline SHA" in text
    assert "Change summary:" in text


def test_review_can_fail_on_quality_regression_without_breaking_semantic_change():
    old = load_document("examples/customer-master.yaml")
    new = deepcopy(old)
    new["mapping"]["fields"][0]["business"].pop("owner")
    policy = {
        "version": 1,
        "name": "quality-regression",
        "requirements": {"owner_required_for": []},
        "quality": {"minimum_score": 0, "max_score_regression": 1},
        "breaking_changes": {"business": "info"},
    }
    report = review_report(old, new, policy)
    assert report["changes"]["passed"] is True
    assert report["quality_delta"]["score"] < -1
    assert report["quality_delta"]["gate"]["passed"] is False
    assert report["passed"] is False


def test_review_markdown_truncates_large_event_lists_but_keeps_counts():
    old = load_document("examples/customer-master.yaml")
    new = load_document("examples/customer-master-v2.yaml")
    report = review_report(old, new, load_document("policies/migration-pragmatic.yaml"))
    original = list(report["changes"]["events"])
    report["changes"]["events"] = original * 6
    text = review_markdown(report, max_items=2)
    assert f"{len(report['changes']['events'])} events" in text
    assert "more** not shown in the compact summary" in text
    assert text.count("- **") == 2


def test_review_markdown_rejects_zero_item_limit():
    old = load_document("examples/customer-master.yaml")
    report = review_report(old, old)
    with pytest.raises(ValueError, match="at least 1"):
        review_markdown(report, max_items=0)


def test_functional_review_exposes_before_after_mapping_intent():
    old = load_document("examples/customer-master.yaml")
    new = load_document("examples/customer-master-v2.yaml")

    report = review_report(old, new, load_document("policies/migration-pragmatic.yaml"))

    item = next(change for change in report["functional_changes"] if change["id"] == "customer-name")
    assert item["before"]["source"]["field"] == "name"
    assert item["after"]["target"]["field"] == "OrganizationBPName1"
    assert item["before"]["transform"] == {"type": "copy"}
    assert item["after"]["transform"]["type"] == "expression"
    assert item["before"]["required_target"] is True
    assert item["after"]["required_target"] is True
    assert item["decision"]["status"] == "review_required"
    assert "transform" in item["decision"]["reasons"]


def test_value_map_only_change_marks_referencing_mapping_for_review():
    old = load_document("examples/customer-master.yaml")
    new = deepcopy(old)
    new["value_maps"]["iso-country"]["DE"] = "GER"

    report = review_report(old, new)

    item = next(change for change in report["functional_changes"] if change["id"] == "customer-country")
    assert item["change_types"] == ["value_map"]
    assert item["severity"] == "warning"
    assert item["value_map_impacts"][0]["map"] == "iso-country"
    assert "referenced_value_map_changed" in item["decision"]["reasons"]


def test_review_can_attach_external_source_provenance_without_changing_mapping():
    old = load_document("examples/customer-master.yaml")
    new = load_document("examples/customer-master-v2.yaml")
    provenance = {
        "fields": {
            "customer-name": {
                "file": "customer-bp-v2.xlsx",
                "sheet": "Mappings",
                "row": 3,
            }
        }
    }

    report = review_report(old, new, new_provenance=provenance)

    item = next(change for change in report["functional_changes"] if change["id"] == "customer-name")
    assert item["after"]["location"] == provenance["fields"]["customer-name"]
    text = review_markdown(report)
    assert "Source location:" in text
    assert "customer-bp-v2.xlsx" in text


def test_review_markdown_contains_functional_intent_details():
    old = load_document("examples/customer-master.yaml")
    new = load_document("examples/customer-master-v2.yaml")
    report = review_report(old, new, load_document("policies/migration-pragmatic.yaml"))

    text = review_markdown(report)

    assert "### Functional review" in text
    assert "customer-name" in text
    assert "Transform:" in text
    assert "Decision: review required" in text
