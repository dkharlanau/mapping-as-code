import json

import jsonschema

from mapping_as_code.adapters import (
    to_enterprise_change_graph,
    to_reconciliation,
    to_transformation_graph,
    to_visual_workbench,
)
from mapping_as_code.io import load_document


def _schema(path: str):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def test_transformation_graph_projection_matches_retained_contract():
    document = load_document("examples/customer-master.yaml")
    projected = to_transformation_graph(document)
    jsonschema.validate(projected, _schema("conformance/transformation-graph/v0.1/transformation-graph.schema.json"))


def test_enterprise_change_graph_snapshot_matches_retained_contract():
    document = load_document("examples/customer-master.yaml")
    projected = to_enterprise_change_graph(document)
    jsonschema.validate(projected, _schema("conformance/enterprise-change-graph/v1/enterprise-change-graph.schema.json"))


def test_visual_workbench_projection_matches_retained_contract():
    document = load_document("examples/customer-master.yaml")
    projected = to_visual_workbench(document)
    jsonschema.validate(projected, _schema("conformance/visual-workbench/v1/visual-workbench.schema.json"))


def test_reconciliation_projection_matches_retained_contract():
    document = load_document("examples/customer-master.yaml")
    projected = to_reconciliation(
        document,
        source_file="legacy.csv",
        target_file="s4.csv",
        source_key="customer_id",
        target_key="BusinessPartner",
    )
    jsonschema.validate(projected, _schema("conformance/reconciliation-as-code/v1/reconciliation.schema.json"))


def test_retained_contract_provenance_has_pinned_blob_sha():
    manifests = [
        "conformance/transformation-graph/v0.1/source.json",
        "conformance/reconciliation-as-code/v1/source.json",
        "conformance/enterprise-change-graph/v1/source.json",
        "conformance/visual-workbench/v1/source.json",
        "conformance/interface-as-code/v1.0/source.json",
    ]
    for path in manifests:
        with open(path, encoding="utf-8") as handle:
            manifest = json.load(handle)
        sha = manifest["source_blob_sha"]
        assert len(sha) == 40
        int(sha, 16)
