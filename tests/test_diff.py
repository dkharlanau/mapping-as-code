from pathlib import Path

from mapping_as_code.diff import diff_documents
from mapping_as_code.io import load_document

ROOT = Path(__file__).parents[1]


def test_diff_detects_added_and_changed_fields():
    before = load_document(ROOT / "examples" / "sap-customer.yaml")
    after = load_document(ROOT / "examples" / "sap-customer-v2.yaml")
    result = diff_documents(before, after)
    assert [item["id"] for item in result.added] == ["postal-code"]
    assert any(item["id"] == "customer-name" for item in result.changed)
    assert result.removed == []
