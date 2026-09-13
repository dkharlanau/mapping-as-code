from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from mapping_as_code.preflight import main as preflight_main


def _write_workbook(path: Path, *, country_target: str = "Country") -> None:
    openpyxl = pytest.importorskip("openpyxl")
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Mappings"
    sheet.append(
        [
            "mapping_id",
            "title",
            "source_system",
            "source_object",
            "target_system",
            "target_object",
            "id",
            "source_field",
            "target_field",
            "transform",
            "reference",
            "expression",
            "required_source",
            "required_target",
            "owner",
            "criticality",
            "rationale",
        ]
    )
    common = [
        "sap-customer-bp",
        "SAP Customer to Business Partner migration mapping",
        "SAP-ECC",
        "Customer",
        "SAP-S4",
        "BusinessPartner",
    ]
    sheet.append(
        common
        + [
            "legacy-id",
            "KUNNR",
            "BusinessPartner",
            "expression",
            "",
            "resolve_via_explicit_identity_crosswalk",
            True,
            True,
            "Master Data",
            "critical",
            "Business identity changes and must be resolved explicitly.",
        ]
    )
    sheet.append(
        common
        + [
            "name",
            "NAME1",
            "OrganizationName1",
            "copy",
            "",
            "",
            True,
            True,
            "Master Data",
            "high",
            "Organization name should survive migration.",
        ]
    )
    sheet.append(
        common
        + [
            "country",
            "LAND1",
            country_target,
            "lookup",
            "country-code",
            "",
            True,
            True,
            "Master Data",
            "high",
            "Country uses an explicit governed value map.",
        ]
    )
    sheet.append(
        common
        + [
            "grouping",
            "KTOKD",
            "BusinessPartnerGrouping",
            "lookup",
            "account-group-to-bp-grouping",
            "",
            True,
            True,
            "Master Data",
            "high",
            "Legacy account group maps explicitly to BP grouping.",
        ]
    )

    value_maps = workbook.create_sheet("ValueMaps")
    value_maps.append(["map", "source", "target"])
    value_maps.append(["country-code", "DE", "DE"])
    value_maps.append(["country-code", "US", "US"])
    value_maps.append(["account-group-to-bp-grouping", "Z001", "ZCUST"])
    value_maps.append(["account-group-to-bp-grouping", "Z002", "ZRETAIL"])
    workbook.save(path)


def _write_data(source: Path, target: Path) -> None:
    source.write_text(
        "KUNNR,NAME1,LAND1,KTOKD\n100001,Alpha Bikes GmbH,DE,Z001\n100002,Northwind Parts Inc,US,Z002\n",
        encoding="utf-8",
    )
    target.write_text(
        "BusinessPartner,LegacyCustomerID,OrganizationName1,Country,BusinessPartnerGrouping\n"
        "900001,100001,Alpha Bikes GmbH,DE,ZCUST\n"
        "900002,100002,Northwind Parts Inc,US,ZRETAIL\n",
        encoding="utf-8",
    )


def test_preflight_emits_canonical_mapping_and_quality_evidence(tmp_path: Path) -> None:
    workbook = tmp_path / "customer-bp.xlsx"
    _write_workbook(workbook)
    output = tmp_path / "preflight"

    code = preflight_main([str(workbook), "--output-dir", str(output)])

    assert code == 0
    assert (output / "mapping.yaml").exists()
    assert (output / "validation-report.json").exists()
    assert (output / "quality-score.json").exists()
    assert (output / "preflight-summary.json").exists()
    summary = json.loads((output / "preflight-summary.json").read_text(encoding="utf-8"))
    assert summary["validation"]["valid"] is True
    assert summary["rac_handoff"]["requested"] is False
    mapping = yaml.safe_load((output / "mapping.yaml").read_text(encoding="utf-8"))
    assert mapping["mapping"]["id"] == "sap-customer-bp"
    assert mapping["mapping"]["title"] == "SAP Customer to Business Partner migration mapping"
    assert mapping["value_maps"]["account-group-to-bp-grouping"]["Z001"] == "ZCUST"


def test_preflight_generates_pinned_rac_handoff_with_explicit_keys(tmp_path: Path) -> None:
    workbook = tmp_path / "customer-bp.xlsx"
    source = tmp_path / "legacy.csv"
    target = tmp_path / "s4.csv"
    _write_workbook(workbook)
    _write_data(source, target)
    output = tmp_path / "preflight"

    code = preflight_main(
        [
            str(workbook),
            "--output-dir",
            str(output),
            "--source-file",
            str(source),
            "--target-file",
            str(target),
            "--source-key",
            "KUNNR",
            "--target-key",
            "LegacyCustomerID",
        ]
    )

    assert code == 0
    reconciliation = yaml.safe_load((output / "reconciliation.yaml").read_text(encoding="utf-8"))
    assert reconciliation["source"]["key"] == "KUNNR"
    assert reconciliation["target"]["key"] == "LegacyCustomerID"
    assert reconciliation["generated_from"]["projection_mode"] == "linked_source"
    artifact = reconciliation["mapping_artifacts"]["mapping-source"]
    assert artifact["file"] == "mapping.yaml"
    assert len(artifact["sha256"]) == 64
    checks = {item["id"]: item for item in reconciliation["checks"]}
    assert "name" in checks
    assert "country" in checks
    assert "grouping" in checks
    assert "legacy-id" not in checks  # expression/crosswalk intent is not reduced to equality


def test_preflight_requires_complete_rac_configuration(tmp_path: Path) -> None:
    workbook = tmp_path / "customer-bp.xlsx"
    _write_workbook(workbook)
    output = tmp_path / "preflight"

    code = preflight_main(
        [
            str(workbook),
            "--output-dir",
            str(output),
            "--source-file",
            str(tmp_path / "legacy.csv"),
        ]
    )

    assert code == 2
    assert (output / "mapping.yaml").exists()
    assert not (output / "reconciliation.yaml").exists()


def test_preflight_reports_corrupted_excel_without_traceback(tmp_path: Path) -> None:
    workbook = tmp_path / "broken.xlsx"
    workbook.write_bytes(b"not-an-xlsx")

    code = preflight_main([str(workbook), "--output-dir", str(tmp_path / "preflight")])

    assert code == 2
