from copy import deepcopy

from mapping_as_code.annotations import github_annotations
from mapping_as_code.io import load_document


def test_annotations_emit_file_level_errors_without_fake_line_numbers():
    document = load_document("examples/customer-master.yaml")
    broken = deepcopy(document)
    broken["mapping"]["fields"][0]["target"]["field"] = ""
    lines = github_annotations(broken, file_path="mappings/customer.yaml")
    assert lines
    assert lines[0].startswith("::error file=mappings/customer.yaml,title=")
    assert "line=" not in lines[0]
    assert "endpoint.field.missing" in lines[0]


def test_annotation_escaping_is_github_command_safe():
    document = load_document("examples/customer-master.yaml")
    broken = deepcopy(document)
    broken["mapping"]["title"] = ""
    lines = github_annotations(
        broken,
        file_path="mappings/customer,main.yaml",
        policy={"version": 1, "name": "x", "requirements": {"title_required": True}},
    )
    assert "%2C" in lines[0]
    assert "::error" in lines[0]
