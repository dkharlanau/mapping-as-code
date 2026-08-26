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
