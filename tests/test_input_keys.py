import pytest

from mapping_as_code.cli import main
from mapping_as_code.io import load_document


@pytest.mark.parametrize("suffix, text", [
    ("yaml", "mapping:\n  id: first\n  id: overwritten\n"),
    ("yaml", "value_maps:\n  country:\n    DE: DE\n    DE: US\n"),
    ("yaml", "mapping: {fields: [{target: {field: A, field: B}}]}\n"),
    ("yaml", "mapping: {<<: {id: first, id: overwritten}}\n"),
    ("json", '{"mapping":{"id":"first","id":"overwritten"}}'),
    ("json", '{"value_maps":{"country":{"DE":"DE","DE":"US"}}}'),
])
def test_duplicate_keys_are_rejected_before_semantic_validation(tmp_path, suffix, text):
    path = tmp_path / f"mapping.{suffix}"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate"):
        load_document(path)


def test_explicit_yaml_merge_override_remains_supported(tmp_path):
    path = tmp_path / "mapping.yaml"
    path.write_text("defaults: &defaults {id: default, title: Default}\nmapping: {<<: *defaults, id: selected}\n")
    assert load_document(path)["mapping"] == {"id": "selected", "title": "Default"}


@pytest.mark.parametrize("text", ["mapping: [", "mapping: {id: first, id: overwritten}"])
def test_invalid_yaml_cli_returns_input_error_without_traceback(tmp_path, capsys, text):
    path = tmp_path / "mapping.yaml"
    path.write_text(text, encoding="utf-8")
    assert main(["validate", str(path), "--format", "json"]) == 2
    result = capsys.readouterr()
    assert result.out == ""
    assert str(path) in result.err
    assert "Traceback" not in result.err
