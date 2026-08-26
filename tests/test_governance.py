from copy import deepcopy

from mapping_as_code.governance import (
    breaking_change_report,
    canonical_hash,
    policy_diagnostics,
    quality_scorecard,
    validation_report,
)
from mapping_as_code.io import load_document


def test_quality_scorecard_is_transparent_and_bounded():
    document = load_document("examples/customer-master.yaml")
    scorecard = quality_scorecard(document)
    assert 0 <= scorecard["score"] <= 100
    assert round(sum(scorecard["dimensions"].values()), 2) == scorecard["score"]
    assert scorecard["counts"]["field_mappings"] == 4
    assert scorecard["counts"]["stable_ids"] == 4


def test_policy_requires_stewardship_for_high_criticality():
    document = load_document("examples/customer-master.yaml")
    broken = deepcopy(document)
    broken["mapping"]["fields"][0]["business"].pop("owner")
    diagnostics = policy_diagnostics(
        broken,
        {
            "version": 1,
            "name": "test",
            "requirements": {
                "owner_required_for": ["high"],
                "rationale_required_for": ["high"],
            },
        },
    )
    assert any(item.code == "policy.owner.missing" for item in diagnostics)


def test_validation_report_can_fail_quality_gate_without_structural_error():
    document = load_document("examples/customer-master.yaml")
    report = validation_report(
        document,
        {"version": 1, "name": "quality-test", "quality": {"minimum_score": 99}},
    )
    assert report["gates"]["no_errors"]["passed"] is True if isinstance(report["gates"]["no_errors"], dict) else report["gates"]["no_errors"] is True
    assert report["gates"]["minimum_quality_score"]["passed"] is False
    assert report["valid"] is False


def test_transform_change_is_breaking_by_default():
    old = load_document("examples/customer-master.yaml")
    new = load_document("examples/customer-master-v2.yaml")
    report = breaking_change_report(old, new)
    assert report["breaking"] is True
    assert report["passed"] is False
    assert any(event["id"] == "customer-name" and event["kind"] == "transform" and event["severity"] == "error" for event in report["events"])


def test_breaking_policy_can_downgrade_transform_change():
    old = load_document("examples/customer-master.yaml")
    new = load_document("examples/customer-master-v2.yaml")
    report = breaking_change_report(
        old,
        new,
        {
            "version": 1,
            "name": "review-only",
            "breaking_changes": {"transform": "warning", "target": "warning", "removed": "warning"},
        },
    )
    assert report["passed"] is True


def test_canonical_hash_is_order_independent_for_object_keys():
    left = {"b": 2, "a": {"y": 1, "x": 0}}
    right = {"a": {"x": 0, "y": 1}, "b": 2}
    assert canonical_hash(left) == canonical_hash(right)
