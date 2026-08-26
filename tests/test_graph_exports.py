from xml.etree import ElementTree

from mapping_as_code.graph_exports import lineage_cypher, lineage_graphml
from mapping_as_code.io import load_document


def test_graphml_is_well_formed_and_contains_mapping_edges():
    document = load_document("examples/customer-master.yaml")
    text = lineage_graphml(document)
    root = ElementTree.fromstring(text)
    ns = {"g": "http://graphml.graphdrawing.org/xmlns"}
    nodes = root.findall(".//g:node", ns)
    edges = root.findall(".//g:edge", ns)
    assert nodes
    assert len(edges) == 4
    assert any(edge.attrib["id"] == "customer-country" for edge in edges)


def test_cypher_is_deterministic_and_preserves_lookup_reference():
    document = load_document("examples/customer-master.yaml")
    first = lineage_cypher(document)
    second = lineage_cypher(document)
    assert first == second
    assert "MappingLineageNode" in first
    assert "MAPS_TO" in first
    assert "iso-country" in first
    assert "customer-country" in first
