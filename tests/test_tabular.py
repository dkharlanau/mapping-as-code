from pathlib import Path

import pytest

from mapping_as_code.core import validate_document
from mapping_as_code.tabular import ImportErrorDetail, import_rows, import_tabular


def rows():
    common = {
        "mapping_id": "customer",
        "source_system": "legacy",
        "source_object": "customer",
        "target_system": "s4",
        "target_object": "bp",
    }
    return [
        {
            **common,
            "id": "id",
            "source_field": "customer_id",
            "target_field": "BusinessPartner",
            "transform": "copy",
            "required_target": "yes",
            "required_source": "yes",
        },
        {
            **common,
            "id": "country",
            "source_field": "country",
            "target_field": "Country",
            "transform": "lookup",
            "reference": "countries",
            "required_target": "x",
        },
        {
            **common,
            "id": "category",
            "target_field": "Category",
            "transform": "constant",
            "value": "2",
            "required_target": True,
        },
    ]


def test_import_rows_builds_valid_contract_with_value_maps():
    document = import_rows(rows(), [{"map": "countries", "source": "DE", "target": "DE"}])
    assert document["mapping"]["target"]["required_fields"] == ["BusinessPartner", "Country", "Category"]
    assert validate_document(document) == []


def test_import_rejects_inconsistent_metadata():
    data = rows()
    data[1]["target_system"] = "other"
    with pytest.raises(ImportErrorDetail, match="inconsistent workbook metadata"):
        import_rows(data)


def test_csv_import(tmp_path: Path):
    source = tmp_path / "mapping.csv"
    source.write_text(
        "mapping_id,source_system,source_object,target_system,target_object,id,source_field,target_field,transform,required_target\n"
        "customer,legacy,customer,s4,bp,id,customer_id,BusinessPartner,copy,true\n",
        encoding="utf-8",
    )
    document = import_tabular(source)
    assert document["mapping"]["fields"][0]["id"] == "id"


def test_csv_rejects_duplicate_headers_before_values_collapse(tmp_path: Path):
    source = tmp_path / "mapping.csv"
    source.write_text(
        "mapping_id,source_system,source_object,target_system,target_object,source_field,target_field,target_field\n"
        "customer,legacy,customer,s4,bp,customer_id,BusinessPartner,OtherTarget\n",
        encoding="utf-8",
    )

    with pytest.raises(ImportErrorDetail) as excinfo:
        import_tabular(source)

    message = str(excinfo.value)
    assert "duplicate header 'target_field' after normalization" in message
    assert f"{source} / row 1 / column 8" in message
    assert f"{source} / row 1 / column 7" in message


def test_csv_rejects_ragged_rows_at_physical_row(tmp_path: Path):
    source = tmp_path / "mapping.csv"
    source.write_text(
        "mapping_id,source_system,source_object,target_system,target_object,source_field,target_field\n"
        "customer,legacy,customer,s4,bp,customer_id\n",
        encoding="utf-8",
    )

    with pytest.raises(ImportErrorDetail, match=r"row 2: expected 7 columns but found 6"):
        import_tabular(source)


def test_csv_multiline_record_preserves_physical_start_row_for_diagnostics(tmp_path: Path):
    source = tmp_path / "mapping.csv"
    source.write_text(
        "mapping_id,source_system,source_object,target_system,target_object,source_field,target_field,rationale\n"
        'customer,legacy,customer,s4,bp,customer_id,BusinessPartner,"line one\nline two"\n'
        "customer,legacy,customer,s4,bp,country,,missing target\n",
        encoding="utf-8",
    )

    with pytest.raises(ImportErrorDetail) as excinfo:
        import_tabular(source)

    assert f"{source} / row 4: target_field is required" in str(excinfo.value)


def test_conflicting_value_map_rows_are_rejected_with_both_locations(tmp_path: Path):
    source = tmp_path / "mapping.csv"
    value_maps = tmp_path / "value-maps.csv"
    source.write_text(
        "mapping_id,source_system,source_object,target_system,target_object,source_field,target_field,transform,reference\n"
        "customer,legacy,customer,s4,bp,country,Country,lookup,countries\n",
        encoding="utf-8",
    )
    value_maps.write_text(
        "map,source,target\n"
        "countries,DE,DE\n"
        "countries,DE,GER\n",
        encoding="utf-8",
    )

    with pytest.raises(ImportErrorDetail) as excinfo:
        import_tabular(source, value_maps)

    message = str(excinfo.value)
    assert "conflicting value-map entry 'countries' / 'DE'" in message
    assert f"{value_maps} / row 2" in message
    assert f"{value_maps} / row 3" in message


def test_exact_duplicate_value_map_rows_are_explicitly_rejected(tmp_path: Path):
    source = tmp_path / "mapping.csv"
    value_maps = tmp_path / "value-maps.csv"
    source.write_text(
        "mapping_id,source_system,source_object,target_system,target_object,source_field,target_field,transform,reference\n"
        "customer,legacy,customer,s4,bp,country,Country,lookup,countries\n",
        encoding="utf-8",
    )
    value_maps.write_text(
        "map,source,target\n"
        "countries,DE,DE\n"
        "countries,DE,DE\n",
        encoding="utf-8",
    )

    with pytest.raises(ImportErrorDetail, match="duplicate value-map entry"):
        import_tabular(source, value_maps)


def test_xlsx_import_with_value_map_sheet(tmp_path: Path):
    openpyxl = pytest.importorskip("openpyxl")
    source = tmp_path / "mapping.xlsx"
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Mappings"
    sheet.append(
        [
            "mapping_id",
            "source_system",
            "source_object",
            "target_system",
            "target_object",
            "id",
            "source_field",
            "target_field",
            "transform",
            "reference",
            "required_target",
        ]
    )
    sheet.append(["customer", "legacy", "customer", "s4", "bp", "country", "country", "Country", "lookup", "countries", True])
    vm = workbook.create_sheet("ValueMaps")
    vm.append(["map", "source", "target"])
    vm.append(["countries", "DE", "DE"])
    workbook.save(source)

    document = import_tabular(source)
    assert document["value_maps"]["countries"]["DE"] == "DE"
    assert validate_document(document) == []


def test_xlsx_rejects_headers_that_collide_after_whitespace_normalization(tmp_path: Path):
    openpyxl = pytest.importorskip("openpyxl")
    source = tmp_path / "mapping.xlsx"
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Mappings"
    sheet.append(
        [
            "mapping_id",
            "source_system",
            "source_object",
            "target_system",
            "target_object",
            "source_field",
            "target_field",
            " target_field ",
        ]
    )
    sheet.append(["customer", "legacy", "customer", "s4", "bp", "customer_id", "BusinessPartner", "OtherTarget"])
    workbook.save(source)

    with pytest.raises(ImportErrorDetail) as excinfo:
        import_tabular(source)

    message = str(excinfo.value)
    assert "duplicate header 'target_field' after normalization" in message
    assert f"{source} / sheet Mappings / row 1 / column 8" in message


def test_xlsx_rejects_formula_without_cached_value_instead_of_treating_it_as_blank(tmp_path: Path):
    openpyxl = pytest.importorskip("openpyxl")
    source = tmp_path / "mapping.xlsx"
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Mappings"
    sheet.append(
        [
            "mapping_id",
            "source_system",
            "source_object",
            "target_system",
            "target_object",
            "source_field",
            "target_field",
        ]
    )
    sheet.append(["customer", "legacy", "customer", "s4", "bp", "customer_id", '="BusinessPartner"'])
    workbook.save(source)

    with pytest.raises(ImportErrorDetail) as excinfo:
        import_tabular(source)

    message = str(excinfo.value)
    assert "formula has no cached value" in message
    assert f"{source} / sheet Mappings / row 2 / column 7" in message


def test_xlsx_preserves_leading_zero_text_ids(tmp_path: Path):
    openpyxl = pytest.importorskip("openpyxl")
    source = tmp_path / "mapping.xlsx"
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Mappings"
    sheet.append(
        [
            "mapping_id",
            "source_system",
            "source_object",
            "target_system",
            "target_object",
            "id",
            "source_field",
            "target_field",
        ]
    )
    sheet.append(["customer", "legacy", "customer", "s4", "bp", "0007", "customer_id", "BusinessPartner"])
    workbook.save(source)

    document = import_tabular(source)

    assert document["mapping"]["fields"][0]["id"] == "0007"


def test_csv_rejects_internal_blank_header_before_row_materialization(tmp_path: Path):
    source = tmp_path / "mapping.csv"
    source.write_text(
        "mapping_id,source_system,source_object,target_system,target_object,,target_field\n"
        "customer,legacy,customer,s4,bp,customer_id,BusinessPartner\n",
        encoding="utf-8",
    )

    with pytest.raises(ImportErrorDetail) as excinfo:
        import_tabular(source)

    message = str(excinfo.value)
    assert "blank header is not allowed" in message
    assert f"{source} / row 1 / column 6" in message


def test_blank_csv_rows_do_not_shift_following_diagnostic_provenance(tmp_path: Path):
    source = tmp_path / "mapping.csv"
    source.write_text(
        "mapping_id,source_system,source_object,target_system,target_object,source_field,target_field\n"
        "customer,legacy,customer,s4,bp,customer_id,BusinessPartner\n"
        "\n"
        "customer,legacy,customer,s4,bp,country,\n",
        encoding="utf-8",
    )

    with pytest.raises(ImportErrorDetail) as excinfo:
        import_tabular(source)

    assert f"{source} / row 4: target_field is required" in str(excinfo.value)


def test_xlsx_rejects_internal_blank_header(tmp_path: Path):
    openpyxl = pytest.importorskip("openpyxl")
    source = tmp_path / "mapping.xlsx"
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Mappings"
    sheet.append(
        [
            "mapping_id",
            "source_system",
            "source_object",
            "target_system",
            "target_object",
            None,
            "target_field",
        ]
    )
    sheet.append(["customer", "legacy", "customer", "s4", "bp", "customer_id", "BusinessPartner"])
    workbook.save(source)

    with pytest.raises(ImportErrorDetail) as excinfo:
        import_tabular(source)

    message = str(excinfo.value)
    assert "blank header is not allowed" in message
    assert f"{source} / sheet Mappings / row 1 / column 6" in message
