from __future__ import annotations

import csv
import re
from itertools import zip_longest
from pathlib import Path
from typing import Any
from zipfile import BadZipFile


class ImportErrorDetail(ValueError):
    """Raised when tabular mapping input is ambiguous or inconsistent."""


class TabularRow(dict[str, Any]):
    """Internal row carrying source provenance without changing the canonical contract."""

    def __init__(
        self,
        values: dict[str, Any],
        *,
        source_path: str | None = None,
        sheet: str | None = None,
        row_number: int | None = None,
    ) -> None:
        super().__init__(values)
        self.source_path = source_path
        self.sheet = sheet
        self.row_number = row_number

    def location(self) -> str | None:
        parts: list[str] = []
        if self.source_path:
            parts.append(self.source_path)
        if self.sheet:
            parts.append(f"sheet {self.sheet}")
        if self.row_number is not None:
            parts.append(f"row {self.row_number}")
        return " / ".join(parts) if parts else None


def _clean(value: Any) -> Any:
    if isinstance(value, str):
        value = value.strip()
        return value if value else None
    return value


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return value != 0
    return str(value).strip().lower() in {"1", "true", "yes", "y", "x", "required"}


def _slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", value.strip()).strip("-")
    return slug or "field"


def _source_location(
    source_path: str | None,
    *,
    sheet: str | None = None,
    row_number: int | None = None,
    column_number: int | None = None,
) -> str:
    parts: list[str] = []
    if source_path:
        parts.append(source_path)
    if sheet:
        parts.append(f"sheet {sheet}")
    if row_number is not None:
        parts.append(f"row {row_number}")
    if column_number is not None:
        parts.append(f"column {column_number}")
    return " / ".join(parts) if parts else "input"


def _row_location(row: dict[str, Any], fallback_index: int, *, label: str = "row") -> str:
    if isinstance(row, TabularRow):
        location = row.location()
        if location:
            return location
    return f"{label} {fallback_index}"


def _normalized_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for row in rows:
        cleaned = {str(key).strip(): _clean(value) for key, value in row.items() if key is not None}
        if not any(value is not None for value in cleaned.values()):
            continue
        if isinstance(row, TabularRow):
            normalized.append(
                TabularRow(
                    cleaned,
                    source_path=row.source_path,
                    sheet=row.sheet,
                    row_number=row.row_number,
                )
            )
        else:
            normalized.append(cleaned)
    return normalized


def _validate_headers(
    values: list[Any] | tuple[Any, ...],
    *,
    source_path: str,
    sheet: str | None = None,
    row_number: int = 1,
    trim_trailing_empty: bool = False,
) -> list[str]:
    headers = [str(value).strip() if value is not None else "" for value in values]
    if trim_trailing_empty:
        while headers and not headers[-1]:
            headers.pop()
    if not headers:
        return []

    seen: dict[str, int] = {}
    for column_number, header in enumerate(headers, start=1):
        location = _source_location(
            source_path,
            sheet=sheet,
            row_number=row_number,
            column_number=column_number,
        )
        if not header:
            raise ImportErrorDetail(f"{location}: blank header is not allowed")
        previous = seen.get(header)
        if previous is not None:
            previous_location = _source_location(
                source_path,
                sheet=sheet,
                row_number=row_number,
                column_number=previous,
            )
            raise ImportErrorDetail(
                f"{location}: duplicate header {header!r} after normalization; "
                f"already defined at {previous_location}"
            )
        seen[header] = column_number
    return headers


def _single(rows: list[dict[str, Any]], column: str) -> str:
    values: dict[str, str] = {}
    for index, row in enumerate(rows, start=2):
        if row.get(column) is None:
            continue
        value = str(row[column])
        values.setdefault(value, _row_location(row, index))
    if not values:
        raise ImportErrorDetail(f"missing required workbook metadata column value: {column}")
    if len(values) > 1:
        details = ", ".join(f"{value!r} at {location}" for value, location in sorted(values.items()))
        raise ImportErrorDetail(f"inconsistent workbook metadata for {column}: {details}")
    return next(iter(values))


def _optional_single(rows: list[dict[str, Any]], column: str) -> str | None:
    values: dict[str, str] = {}
    for index, row in enumerate(rows, start=2):
        if row.get(column) is None:
            continue
        value = str(row[column])
        values.setdefault(value, _row_location(row, index))
    if len(values) > 1:
        details = ", ".join(f"{value!r} at {location}" for value, location in sorted(values.items()))
        raise ImportErrorDetail(f"inconsistent workbook metadata for {column}: {details}")
    return next(iter(values)) if values else None


def _read_csv(path: Path) -> list[dict[str, Any]]:
    source_path = str(path)
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        try:
            header_values = next(reader)
        except StopIteration:
            return []
        except csv.Error as exc:
            raise ImportErrorDetail(f"{source_path} / row 1: invalid CSV: {exc}") from exc

        headers = _validate_headers(header_values, source_path=source_path)
        rows: list[dict[str, Any]] = []
        while True:
            start_line = reader.line_num + 1
            try:
                values = next(reader)
            except StopIteration:
                break
            except csv.Error as exc:
                raise ImportErrorDetail(f"{source_path} / row {start_line}: invalid CSV: {exc}") from exc

            if not values or not any(_clean(value) is not None for value in values):
                continue
            if len(values) != len(headers):
                raise ImportErrorDetail(
                    f"{source_path} / row {start_line}: expected {len(headers)} columns "
                    f"but found {len(values)}"
                )
            rows.append(
                TabularRow(
                    {header: values[index] for index, header in enumerate(headers)},
                    source_path=source_path,
                    row_number=start_line,
                )
            )
    return _normalized_rows(rows)


def _resolved_excel_value(formula_cell: Any, cached_cell: Any, *, source_path: str, sheet: str) -> Any:
    if getattr(formula_cell, "data_type", None) != "f":
        return formula_cell.value

    cached_value = cached_cell.value if cached_cell is not None else None
    if cached_value is None:
        raise ImportErrorDetail(
            f"{_source_location(source_path, sheet=sheet, row_number=formula_cell.row, column_number=formula_cell.column)}: "
            "formula has no cached value; recalculate and save the workbook before import"
        )
    return cached_value


def _sheet_rows(sheet: Any, cached_sheet: Any, *, source_path: str) -> list[dict[str, Any]]:
    formula_iterator = sheet.iter_rows()
    cached_iterator = cached_sheet.iter_rows()
    try:
        header_cells = next(formula_iterator)
    except StopIteration:
        return []
    try:
        next(cached_iterator)
    except StopIteration:
        pass

    for cell in header_cells:
        if getattr(cell, "data_type", None) == "f":
            raise ImportErrorDetail(
                f"{_source_location(source_path, sheet=sheet.title, row_number=cell.row, column_number=cell.column)}: "
                "formula headers are not supported"
            )

    headers = _validate_headers(
        [cell.value for cell in header_cells],
        source_path=source_path,
        sheet=sheet.title,
        row_number=1,
        trim_trailing_empty=True,
    )
    if not headers:
        return []

    rows: list[dict[str, Any]] = []
    width = len(headers)
    for formula_cells, cached_cells in zip_longest(formula_iterator, cached_iterator, fillvalue=()):
        formula_cells = tuple(formula_cells)
        cached_cells = tuple(cached_cells)
        if not formula_cells and not cached_cells:
            continue

        row_number = formula_cells[0].row if formula_cells else cached_cells[0].row
        for cell in formula_cells[width:]:
            if cell.value is not None:
                raise ImportErrorDetail(
                    f"{_source_location(source_path, sheet=sheet.title, row_number=row_number, column_number=cell.column)}: "
                    f"data exists beyond the {width} declared header columns"
                )

        cached_by_column = {cell.column: cell for cell in cached_cells}
        values: list[Any] = []
        for index in range(width):
            if index >= len(formula_cells):
                values.append(None)
                continue
            formula_cell = formula_cells[index]
            cached_cell = cached_by_column.get(formula_cell.column)
            values.append(
                _resolved_excel_value(
                    formula_cell,
                    cached_cell,
                    source_path=source_path,
                    sheet=sheet.title,
                )
            )

        if not any(_clean(value) is not None for value in values):
            continue
        rows.append(
            TabularRow(
                {header: values[index] for index, header in enumerate(headers)},
                source_path=source_path,
                sheet=sheet.title,
                row_number=row_number,
            )
        )
    return _normalized_rows(rows)


def _read_xlsx(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    try:
        from openpyxl import load_workbook
        from openpyxl.utils.exceptions import InvalidFileException
    except ImportError as exc:
        raise ImportErrorDetail(
            "XLSX import requires the optional dependency: pip install 'mapping-as-code[excel]'"
        ) from exc

    source_path = str(path)
    formula_workbook = None
    cached_workbook = None
    try:
        formula_workbook = load_workbook(path, read_only=True, data_only=False)
        cached_workbook = load_workbook(path, read_only=True, data_only=True)
    except (BadZipFile, InvalidFileException) as exc:
        if formula_workbook is not None:
            formula_workbook.close()
        if cached_workbook is not None:
            cached_workbook.close()
        raise ImportErrorDetail(f"invalid or corrupted Excel workbook: {path}") from exc

    try:
        mapping_sheet = formula_workbook["Mappings"] if "Mappings" in formula_workbook.sheetnames else formula_workbook.active
        cached_mapping_sheet = cached_workbook[mapping_sheet.title]
        mappings = _sheet_rows(mapping_sheet, cached_mapping_sheet, source_path=source_path)

        if "ValueMaps" in formula_workbook.sheetnames:
            value_map_sheet = formula_workbook["ValueMaps"]
            cached_value_map_sheet = cached_workbook["ValueMaps"]
            value_maps = _sheet_rows(value_map_sheet, cached_value_map_sheet, source_path=source_path)
        else:
            value_maps = []
        return mappings, value_maps
    finally:
        if formula_workbook is not None:
            formula_workbook.close()
        if cached_workbook is not None:
            cached_workbook.close()


def read_tabular(
    path: str | Path, value_maps_path: str | Path | None = None
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    source = Path(path)
    if source.suffix.lower() in {".xlsx", ".xlsm"}:
        mappings, value_maps = _read_xlsx(source)
        if value_maps_path:
            value_maps = _read_csv(Path(value_maps_path))
        return mappings, value_maps
    if source.suffix.lower() != ".csv":
        raise ImportErrorDetail("supported tabular formats are .csv, .xlsx, and .xlsm")
    mappings = _read_csv(source)
    value_maps = _read_csv(Path(value_maps_path)) if value_maps_path else []
    return mappings, value_maps


def import_rows(
    rows: list[dict[str, Any]], value_map_rows: list[dict[str, Any]] | None = None
) -> dict[str, Any]:
    rows = _normalized_rows(rows)
    if not rows:
        raise ImportErrorDetail("mapping workbook contains no data rows")

    mapping_id = _single(rows, "mapping_id")
    title = _optional_single(rows, "title")
    source_system = _single(rows, "source_system")
    source_object = _single(rows, "source_object")
    target_system = _single(rows, "target_system")
    target_object = _single(rows, "target_object")

    fields: list[dict[str, Any]] = []
    required_targets: list[str] = []
    required_sources: list[str] = []

    for index, row in enumerate(rows, start=2):
        location = _row_location(row, index)
        target_field = row.get("target_field")
        if target_field is None:
            raise ImportErrorDetail(f"{location}: target_field is required")

        transform_type = str(row.get("transform") or "copy").strip().lower()
        source_field = row.get("source_field")
        if transform_type != "constant" and source_field is None:
            raise ImportErrorDetail(f"{location}: source_field is required for {transform_type} transform")

        field_id = row.get("id")
        if field_id is None:
            left = str(source_field) if source_field is not None else "constant"
            field_id = _slug(f"{left}-to-{target_field}")

        field: dict[str, Any] = {
            "id": str(field_id),
            "target": {"field": str(target_field)},
            "transform": {"type": transform_type},
        }
        if source_field is not None:
            field["source"] = {"field": str(source_field)}

        if transform_type == "lookup" and row.get("reference") is not None:
            field["transform"]["reference"] = str(row["reference"])
        if transform_type == "constant":
            if row.get("value") is None:
                raise ImportErrorDetail(f"{location}: constant transform requires value")
            field["transform"]["value"] = row["value"]
        if transform_type == "expression" and row.get("expression") is not None:
            field["transform"]["expression"] = str(row["expression"])

        rules: dict[str, Any] = {}
        if _as_bool(row.get("required_target")):
            required_targets.append(str(target_field))
            rules["required"] = True
        if _as_bool(row.get("required_source")) and source_field is not None:
            required_sources.append(str(source_field))
        if rules:
            field["rules"] = rules

        business = {
            key: row.get(key)
            for key in ("owner", "criticality", "rationale")
            if row.get(key) is not None
        }
        if business:
            field["business"] = business

        if _as_bool(row.get("allow_multiple_sources")):
            field["allow_multiple_sources"] = True
        fields.append(field)

    value_maps: dict[str, dict[Any, Any]] = {}
    value_map_locations: dict[str, dict[Any, str]] = {}
    normalized_value_maps = _normalized_rows(value_map_rows or [])
    for index, row in enumerate(normalized_value_maps, start=2):
        location = _row_location(row, index, label="value-map row")
        name = row.get("map")
        source_value = row.get("source")
        if name is None or source_value is None or "target" not in row or row.get("target") is None:
            raise ImportErrorDetail(f"{location}: map, source, and target are required")

        map_name = str(name)
        target_value = row["target"]
        current_map = value_maps.setdefault(map_name, {})
        current_locations = value_map_locations.setdefault(map_name, {})
        if source_value in current_map:
            previous_location = current_locations[source_value]
            if current_map[source_value] == target_value:
                raise ImportErrorDetail(
                    f"{location}: duplicate value-map entry {map_name!r} / {source_value!r}; "
                    f"already defined at {previous_location}"
                )
            raise ImportErrorDetail(
                f"{location}: conflicting value-map entry {map_name!r} / {source_value!r}: "
                f"{current_map[source_value]!r} at {previous_location} versus {target_value!r}"
            )
        current_map[source_value] = target_value
        current_locations[source_value] = location

    mapping: dict[str, Any] = {
        "id": mapping_id,
        "source": {
            "system": source_system,
            "object": source_object,
            "required_fields": list(dict.fromkeys(required_sources)),
        },
        "target": {
            "system": target_system,
            "object": target_object,
            "required_fields": list(dict.fromkeys(required_targets)),
        },
        "fields": fields,
    }
    if title is not None:
        mapping["title"] = title

    document: dict[str, Any] = {
        "schema_version": "0.1",
        "mapping": mapping,
    }
    if value_maps:
        document["value_maps"] = value_maps
    return document


def _row_provenance(row: dict[str, Any]) -> dict[str, Any] | None:
    if not isinstance(row, TabularRow):
        return None
    location: dict[str, Any] = {}
    if row.source_path:
        location["file"] = row.source_path
    if row.sheet:
        location["sheet"] = row.sheet
    if row.row_number is not None:
        location["row"] = row.row_number
    return location or None


def tabular_provenance(
    document: dict[str, Any],
    rows: list[dict[str, Any]],
    value_map_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    normalized_rows = _normalized_rows(rows)
    mapping = document.get("mapping") if isinstance(document.get("mapping"), dict) else {}
    fields = mapping.get("fields") if isinstance(mapping.get("fields"), list) else []
    field_locations: dict[str, dict[str, Any]] = {}
    for field, row in zip(fields, normalized_rows):
        if not isinstance(field, dict) or field.get("id") is None:
            continue
        location = _row_provenance(row)
        if location:
            field_locations[str(field["id"])] = location

    value_map_locations: list[dict[str, Any]] = []
    for row in _normalized_rows(value_map_rows or []):
        location = _row_provenance(row)
        if location and row.get("map") is not None and row.get("source") is not None:
            value_map_locations.append(
                {
                    "map": str(row["map"]),
                    "source": str(row["source"]),
                    "location": location,
                }
            )

    return {
        "provenance_version": 1,
        "mapping_id": mapping.get("id"),
        "fields": field_locations,
        "value_maps": value_map_locations,
    }


def import_tabular_with_provenance(
    path: str | Path,
    value_maps_path: str | Path | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    rows, value_maps = read_tabular(path, value_maps_path=value_maps_path)
    document = import_rows(rows, value_maps)
    return document, tabular_provenance(document, rows, value_maps)


def import_tabular(path: str | Path, value_maps_path: str | Path | None = None) -> dict[str, Any]:
    document, _ = import_tabular_with_provenance(path, value_maps_path=value_maps_path)
    return document
