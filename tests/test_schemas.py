import json

import jsonschema

from mapping_as_code.artifacts import release_bundle
from mapping_as_code.composition import compose_manifest
from mapping_as_code.governance import validation_report
from mapping_as_code.io import load_document


def _schema(path: str):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def test_policy_packs_match_published_schema():
    schema = _schema("schema/governance-policy.schema.json")
    jsonschema.validate(load_document("policies/enterprise-strict.yaml"), schema)
    jsonschema.validate(load_document("policies/migration-pragmatic.yaml"), schema)


def test_validation_report_matches_published_schema():
    document = load_document("examples/customer-master.yaml")
    report = validation_report(document, load_document("policies/migration-pragmatic.yaml"))
    jsonschema.validate(report, _schema("schema/validation-report.schema.json"))


def test_release_bundle_matches_published_schema():
    document = load_document("examples/customer-master.yaml")
    bundle = release_bundle(
        document,
        source_name="customer-master.yaml",
        source_hash="b" * 64,
        policy=load_document("policies/migration-pragmatic.yaml"),
    )
    jsonschema.validate(bundle, _schema("schema/release-bundle.schema.json"))


def test_composition_manifest_and_fragments_match_published_schemas():
    jsonschema.validate(
        load_document("examples/composition/customer.composition.yaml"),
        _schema("schema/composition-manifest.schema.json"),
    )
    fragment_schema = _schema("schema/mapping-fragment.schema.json")
    jsonschema.validate(load_document("examples/composition/country.fragment.yaml"), fragment_schema)
    jsonschema.validate(load_document("examples/composition/address.fragment.yaml"), fragment_schema)


def test_composed_result_is_a_normal_mapping_contract():
    document, _ = compose_manifest("examples/composition/customer.composition.yaml")
    jsonschema.validate(document, _schema("schema/mapping.schema.json"))
