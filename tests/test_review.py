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
