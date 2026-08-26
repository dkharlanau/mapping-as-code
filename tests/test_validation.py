from copy import deepcopy
from pathlib import Path

from mapping_as_code.io import load_document
from mapping_as_code.validation import validate_document

EXAMPLE = Path(__file__).parents[1] / "examples" / "sap-customer.yaml"


def test_example_is_valid():
    assert validate_document(load_document(EXAMPLE)) == []


def test_missing_value_map_is_detected():
    document = load_document(EXAMPLE)
    document["fields"][2]["transform"]["reference"] = "does-not-exist"
    findings = validate_document(document)
    assert any(finding.code == "MISSING_VALUE_MAP" for finding in findings)


def test_target_collision_is_detected():
    document = load_document(EXAMPLE)
    duplicate = deepcopy(document["fields"][0])
    duplicate["id"] = "another-id"
    document["fields"].append(duplicate)
    findings = validate_document(document)
    assert any(finding.code == "TARGET_COLLISION" for finding in findings)
