import json

import jsonschema

from mapping_as_code.contracts import TARGET_CONTRACTS
from mapping_as_code.ecosystem import ecosystem_bundle
from mapping_as_code.io import load_document


def test_complete_ecosystem_bundle_is_schema_valid_and_pins_target_contracts():
    mapping = load_document("examples/customer-master-v2.yaml")
    baseline = load_document("examples/customer-master.yaml")
    interface = load_document("examples/customer-interface.yaml")
    bundle = ecosystem_bundle(
        mapping,
        source_name="customer-master-v2.yaml",
        source_hash="c" * 64,
        policy=load_document("policies/migration-pragmatic.yaml"),
        baseline=baseline,
        reconciliation={
            "source_file": "legacy.csv",
            "target_file": "s4.csv",
            "source_key": "customer_id",
            "target_key": "BusinessPartner",
        },
        interface_document=interface,
        mapping_uri="mappings/customer-master-v2.yaml",
        revision="main@v2",
    )
    with open("schema/ecosystem-bundle.schema.json", encoding="utf-8") as handle:
        jsonschema.validate(bundle, json.load(handle))

    assert set(bundle["artifacts"]) == {
        "mapping-release",
        "transformation-graph",
        "enterprise-change-graph",
        "visual-workbench",
        "enterprise-change-transition",
        "reconciliation-as-code",
        "interface-as-code",
    }
    for name in (
        "transformation-graph",
        "enterprise-change-graph",
        "visual-workbench",
        "reconciliation-as-code",
        "interface-as-code",
    ):
        artifact = bundle["artifacts"][name]
        assert artifact["contract"]["source_blob_sha"] == TARGET_CONTRACTS[name]["source_blob_sha"]


def test_minimal_ecosystem_bundle_does_not_invent_runtime_contracts():
    mapping = load_document("examples/customer-master.yaml")
    bundle = ecosystem_bundle(mapping, source_name="customer-master.yaml", source_hash="d" * 64)
    assert set(bundle["artifacts"]) == {
        "mapping-release",
        "transformation-graph",
        "enterprise-change-graph",
        "visual-workbench",
    }
    assert "reconciliation-as-code" not in bundle["artifacts"]
    assert "interface-as-code" not in bundle["artifacts"]
