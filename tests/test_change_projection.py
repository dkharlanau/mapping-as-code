import json
from copy import deepcopy

import jsonschema

from mapping_as_code.change_projection import to_enterprise_change_transition
from mapping_as_code.io import load_document


def _schema():
    with open("conformance/enterprise-change-graph/v1/enterprise-change-graph.schema.json", encoding="utf-8") as handle:
        return json.load(handle)


def test_mapping_revision_becomes_change_graph_seeds_and_is_schema_valid():
    old = load_document("examples/customer-master.yaml")
    new = load_document("examples/customer-master-v2.yaml")
    graph = to_enterprise_change_transition(old, new)
    jsonschema.validate(graph, _schema())
    change = graph["changes"][0]
    assert "mapping:legacy-customer-to-s4-business-partner:customer-name" in change["seeds"]
    assert "mapping:legacy-customer-to-s4-business-partner:customer-city" in change["seeds"]
    by_id = {node["id"]: node for node in graph["nodes"]}
    assert by_id["mapping:legacy-customer-to-s4-business-partner:customer-name"]["metadata"]["transition_status"] == "changed"
    assert by_id["mapping:legacy-customer-to-s4-business-partner:customer-city"]["metadata"]["transition_status"] == "added"


def test_removed_mapping_rule_stays_in_transition_topology_as_seed():
    old = load_document("examples/customer-master.yaml")
    new = deepcopy(old)
    new["mapping"]["fields"] = [item for item in new["mapping"]["fields"] if item["id"] != "customer-country"]
    graph = to_enterprise_change_transition(old, new)
    jsonschema.validate(graph, _schema())
    removed_id = "mapping:legacy-customer-to-s4-business-partner:customer-country"
    assert removed_id in graph["changes"][0]["seeds"]
    by_id = {node["id"]: node for node in graph["nodes"]}
    assert by_id[removed_id]["metadata"]["transition_status"] == "removed"
    assert any(edge["source"] == removed_id and edge["metadata"].get("transition_status") == "removed" for edge in graph["edges"])


def test_transition_rejects_different_mapping_identity():
    old = load_document("examples/customer-master.yaml")
    new = deepcopy(old)
    new["mapping"]["id"] = "different-contract"
    try:
        to_enterprise_change_transition(old, new)
    except ValueError as exc:
        assert "same mapping.id" in str(exc)
    else:
        raise AssertionError("expected mapping identity mismatch to fail")
