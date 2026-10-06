from __future__ import annotations

import json
from pathlib import Path

import yaml

from mapping_as_code.preflight import main as preflight_main


FIXTURES = Path("examples/sap-s4hana/customer-bp-mapping")
POLICY = Path("policies/migration-pragmatic.yaml")


def test_sap_customer_bp_review_lifecycle(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline"
    broken = tmp_path / "broken"
    corrected = tmp_path / "corrected"
    malformed = tmp_path / "malformed"

    assert (
        preflight_main(
            [
                str(FIXTURES / "customer-bp-mapping.xlsx"),
                "--policy",
                str(POLICY),
                "--output-dir",
                str(baseline),
            ]
        )
        == 0
    )

    assert (
        preflight_main(
            [
                str(FIXTURES / "customer-bp-mapping-malformed.csv"),
                "--output-dir",
                str(malformed),
            ]
        )
        == 2
    )
    assert not (malformed / "mapping.yaml").exists()

    assert (
        preflight_main(
            [
                str(FIXTURES / "customer-bp-mapping-v2-broken.csv"),
                "--value-maps",
                str(FIXTURES / "customer-bp-value-maps-v2-broken.csv"),
                "--policy",
                str(POLICY),
                "--baseline",
                str(baseline / "mapping.yaml"),
                "--baseline-provenance",
                str(baseline / "import-provenance.json"),
                "--output-dir",
                str(broken),
            ]
        )
        == 1
    )

    broken_review = json.loads((broken / "semantic-review.json").read_text(encoding="utf-8"))
    assert broken_review["passed"] is False
    assert broken_review["current"]["validation"]["valid"] is False
    broken_changes = {item["id"]: item for item in broken_review["functional_changes"]}
    assert "transform" in broken_changes["name"]["change_types"]
    assert "target" in broken_changes["country"]["change_types"]
    assert "value_map" in broken_changes["country"]["change_types"]
    assert broken_changes["country"]["after"]["owner"] is None
    assert broken_changes["country"]["after"]["location"]["row"] == 4

    assert (
        preflight_main(
            [
                str(FIXTURES / "customer-bp-mapping-v2-corrected.csv"),
                "--value-maps",
                str(FIXTURES / "customer-bp-value-maps-v2-corrected.csv"),
                "--policy",
                str(POLICY),
                "--baseline",
                str(baseline / "mapping.yaml"),
                "--baseline-provenance",
                str(baseline / "import-provenance.json"),
                "--source-file",
                str(FIXTURES / "legacy-customers-v2.csv"),
                "--target-file",
                str(FIXTURES / "s4-business-partners-v2.csv"),
                "--source-key",
                "KUNNR",
                "--target-key",
                "LegacyCustomerID",
                "--output-dir",
                str(corrected),
            ]
        )
        == 0
    )

    corrected_review = json.loads((corrected / "semantic-review.json").read_text(encoding="utf-8"))
    corrected_summary = json.loads((corrected / "preflight-summary.json").read_text(encoding="utf-8"))
    reconciliation = yaml.safe_load((corrected / "reconciliation.yaml").read_text(encoding="utf-8"))

    assert corrected_review["passed"] is True
    assert corrected_summary["validation"]["valid"] is True
    corrected_changes = {item["id"]: item for item in corrected_review["functional_changes"]}
    assert corrected_changes["city"]["change_types"] == ["added"]
    assert "value_map" in corrected_changes["country"]["change_types"]
    assert corrected_changes["country"]["severity"] == "info"
    check_ids = {item["id"] for item in reconciliation["checks"]}
    assert "city" in check_ids
    assert "legacy-id" not in check_ids
