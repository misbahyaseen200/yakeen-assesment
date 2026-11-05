"""Validation of a raw extract before it is loaded.

The loader refuses to load an extract that fails a *hard* check (the file would corrupt the
raw layer or the respondent key) and records *soft* findings (schema surprises such as an
extra column) without blocking, because raw must preserve what was received.

Hard failures  -> ValidationError is raised, nothing is written.
Soft findings  -> returned in ValidationReport.warnings and persisted to raw.load_runs.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

KEY_COLUMNS = ("year", "id_")
ALLOWED_VALUE_TYPES = (str, int, float, type(None))


class ValidationError(Exception):
    """A hard validation failure; the extract must not be loaded."""


@dataclass
class ValidationReport:
    extract_name: str
    rows_read: int = 0
    columns: list[str] = field(default_factory=list)
    unexpected_columns: list[str] = field(default_factory=list)
    missing_columns: list[str] = field(default_factory=list)
    years_found: dict[str, int] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps(self.__dict__, default=str)


@dataclass
class ParsedExtract:
    """The parsed file in row form, plus its embedded metadata."""

    rows: list[dict[str, Any]]
    variables: list[dict[str, Any]]  # [{'name','label','position'}]
    codes: list[dict[str, Any]]  # [{'variable_name','code','label'}]


def parse_extract_file(path: Path) -> ParsedExtract:
    """Parse ``post_processing_output.json`` (column-oriented) into rows.

    Raises ValidationError when the file is not JSON or does not have the expected shape.
    """
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:  # e.g. GSS.json, which is a Python repr
        raise ValidationError(f"{path.name} is not valid JSON: {exc}") from exc
    if not isinstance(doc, dict) or "data" not in doc:
        raise ValidationError(f"{path.name}: top-level object must contain a 'data' key")

    data = doc["data"]
    if not isinstance(data, dict) or not data:
        raise ValidationError(f"{path.name}: 'data' must be a non-empty object of column arrays")
    lengths = {col: len(vals) for col, vals in data.items()}
    if len(set(lengths.values())) != 1:
        raise ValidationError(f"{path.name}: column arrays have unequal lengths: {lengths}")
    n = next(iter(lengths.values()))
    rows = [{col: data[col][i] for col in data} for i in range(n)]

    variables = [
        {"name": v.get("name"), "label": v.get("label"), "position": int(pos)}
        for pos, v in sorted(doc.get("variables", {}).items(), key=lambda kv: int(kv[0]))
    ]
    codes: list[dict[str, Any]] = []
    for entry in doc.get("codes", {}).values():
        for code, label in entry.get("CodeLabel", {}).items():
            try:
                code_int = int(code)
            except ValueError as exc:
                raise ValidationError(
                    f"{path.name}: non-integer code {code!r} for {entry.get('variable_name')}"
                ) from exc
            codes.append({"variable_name": entry.get("variable_name"), "code": code_int, "label": label})
    return ParsedExtract(rows=rows, variables=variables, codes=codes)


def validate_rows(
    extract_name: str,
    rows: list[dict[str, Any]],
    expected_years: list[int],
    expected_variables: list[str],
    expected_rows: int | None = None,
) -> ValidationReport:
    report = ValidationReport(extract_name=extract_name, rows_read=len(rows))
    if not rows:
        raise ValidationError(f"{extract_name}: extract contains no rows")

    columns = list(rows[0].keys())
    report.columns = columns
    for key in KEY_COLUMNS:
        if key not in columns:
            raise ValidationError(f"{extract_name}: key column {key!r} missing")

    report.unexpected_columns = sorted(set(columns) - set(expected_variables))
    report.missing_columns = sorted(set(expected_variables) - set(columns))
    if report.unexpected_columns:
        report.warnings.append(f"unexpected columns loaded but not modelled: {report.unexpected_columns}")
    if report.missing_columns:
        report.warnings.append(f"expected columns absent: {report.missing_columns}")

    # Value types: only JSON scalars; anything nested means the file shape changed.
    for i, row in enumerate(rows):
        for col, val in row.items():
            if not isinstance(val, ALLOWED_VALUE_TYPES):
                raise ValidationError(f"{extract_name}: row {i} column {col!r} has non-scalar value {val!r}")

    # Keys: year must be one of the declared years, id_ an integer, (year, id_) unique.
    keys: Counter = Counter()
    years: Counter = Counter()
    for i, row in enumerate(rows):
        try:
            year = int(row["year"])
            id_ = int(row["id_"])
        except (TypeError, ValueError) as exc:
            raise ValidationError(f"{extract_name}: row {i} has non-integer key {row['year']!r}/{row['id_']!r}") from exc
        if year not in expected_years:
            raise ValidationError(f"{extract_name}: row {i} has year {year}, expected one of {expected_years}")
        keys[(year, id_)] += 1
        years[str(year)] += 1
    dupes = [k for k, c in keys.items() if c > 1]
    if dupes:
        raise ValidationError(f"{extract_name}: {len(dupes)} duplicate (year, id_) keys, e.g. {dupes[:3]}")
    report.years_found = dict(sorted(years.items()))
    missing_years = [y for y in expected_years if str(y) not in years]
    if missing_years:
        report.warnings.append(f"declared years with no rows: {missing_years}")

    if expected_rows is not None and len(rows) != expected_rows:
        report.warnings.append(f"row count {len(rows)} differs from declared {expected_rows}")
    return report
