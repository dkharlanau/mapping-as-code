import json

import jsonschema

from mapping_as_code.artifacts import release_bundle
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
