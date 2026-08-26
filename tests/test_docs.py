from pathlib import Path

from mapping_as_code.docs import render_markdown
from mapping_as_code.io import load_document

ROOT = Path(__file__).parents[1]


def test_markdown_contains_mapping_table_and_value_map():
    output = render_markdown(load_document(ROOT / "examples" / "sap-customer.yaml"))
    assert "# legacy-customer-to-s4-business-partner" in output
    assert "| customer-id | KNA1.KUNNR | BusinessPartner | copy | yes |" in output
    assert "### country-code" in output
