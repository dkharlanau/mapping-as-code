import json
from copy import deepcopy

import jsonschema
import pytest

from mapping_as_code.governance import canonical_hash
from mapping_as_code.interface_binding import bind_interface_contract
from mapping_as_code.io import load_document


def _interface_schema():
    with open("conformance/interface-as-code/v1.0/interface.schema.json", encoding="utf-8") as handle:
        return json.load(handle)


def test_binding_adds_official_mapping_artifact_ref_and_stays_schema_valid():
    interface = load_document("examples/customer-interface.yaml")
    mapping = load_document("examples/customer-master.yaml")
    bound = bind_interface_contract(
        interface,
        mapping,
        mapping_uri="mappings/customer-master.yaml",
        revision="main@abc123",
    )
    ref = bound["mapping"]["ref"]
    assert ref == {
        "kind": "mapping-as-code",
        "uri": "mappings/customer-master.yaml",
        "revision": "main@abc123",
        "sha256": canonical_hash(mapping),
    }
    jsonschema.validate(bound, _interface_schema())


def test_binding_rejects_endpoint_mismatch_by_default():
    interface = load_document("examples/customer-interface.yaml")
    mapping = load_document("examples/customer-master.yaml")
    wrong = deepcopy(interface)
    wrong["interface"]["target"]["object"] = "sales-order"
    with pytest.raises(ValueError, match="endpoint mismatch"):
        bind_interface_contract(wrong, mapping, mapping_uri="mappings/customer-master.yaml")


def test_binding_can_explicitly_allow_endpoint_mismatch():
    interface = load_document("examples/customer-interface.yaml")
    mapping = load_document("examples/customer-master.yaml")
    wrong = deepcopy(interface)
    wrong["interface"]["target"]["object"] = "sales-order"
    bound = bind_interface_contract(
        wrong,
        mapping,
        mapping_uri="mappings/customer-master.yaml",
        allow_endpoint_mismatch=True,
    )
    assert bound["mapping"]["ref"]["kind"] == "mapping-as-code"
