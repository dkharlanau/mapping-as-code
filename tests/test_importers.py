from pathlib import Path

from mapping_as_code.importers import import_tabular
from mapping_as_code.validation import validate_document

ROOT = Path(__file__).parents[1]


def test_csv_import_produces_canonical_document():
    document = import_tabular(
        ROOT / "examples" / "import-template.csv",
        name="imported-customer-map",
        source_system="LEGACY",
        source_object="CUSTOMER",
        target_system="S4",
        target_object="BP",
    )
    assert len(document["fields"]) == 3
    assert document["fields"][2]["transform"]["reference"] == "country-code"
    assert validate_document(document) == []
