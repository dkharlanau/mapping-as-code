from copy import deepcopy

from mapping_as_code.io import load_document
from mapping_as_code.sarif import sarif_report


def test_sarif_uses_artifact_location_without_fake_region():
    document = load_document("examples/customer-master.yaml")
    broken = deepcopy(document)
    broken["mapping"]["fields"][0]["target"]["field"] = ""
    report = sarif_report(broken, artifact_uri="mappings/customer.yaml")
    assert report["version"] == "2.1.0"
    result = report["runs"][0]["results"][0]
    location = result["locations"][0]["physicalLocation"]
    assert location["artifactLocation"]["uri"] == "mappings/customer.yaml"
    assert "region" not in location
    assert result["level"] == "error"


def test_sarif_is_empty_but_valid_shape_for_clean_mapping():
    document = load_document("examples/customer-master.yaml")
    report = sarif_report(document, artifact_uri="examples/customer-master.yaml")
    run = report["runs"][0]
    assert run["results"] == []
    assert run["tool"]["driver"]["name"] == "Mapping as Code"
    assert run["properties"]["valid"] is True
