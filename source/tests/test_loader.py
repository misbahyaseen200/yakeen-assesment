"""Tests for the raw loader: idempotency, order independence and bad-input handling.

They run against a temporary DuckDB file and the real committed extracts (fast: ~12k rows).
Run with:  uv run pytest
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import duckdb
import pytest

from source.pipeline.config import REPO_ROOT, Settings
from source.pipeline.load_extracts import connect, load_all, load_extract
from source.pipeline.validate import ValidationError, parse_extract_file, validate_rows

RAW_DIR = REPO_ROOT / "source" / "data" / "raw"
MANIFEST = REPO_ROOT / "source" / "data" / "extracts.json"


def _settings(tmp_path: Path) -> Settings:
    return Settings(
        db_path=tmp_path / "test.duckdb",
        raw_dir=RAW_DIR,
        extracts_manifest=MANIFEST,
        log_dir=tmp_path / "logs",
        log_level="WARNING",
        dbt_dir=REPO_ROOT / "dbt",
        dbt_target="dev",
    )


def _fingerprint(db_path: Path) -> tuple:
    """Order-independent digest of the raw rows: count plus a hash over every row."""
    conn = duckdb.connect(str(db_path), read_only=True)
    try:
        return conn.execute(
            """
            select count(*),
                   count(distinct (extract_name, year, id_)),
                   md5(string_agg(extract_name || '|' || year || '|' || id_ || '|' || record::varchar, '\n'
                                  order by extract_name, year, id_))
            from raw.extract_rows
            """
        ).fetchone()
    finally:
        conn.close()


# --- idempotency ---------------------------------------------------------------------------


def test_loading_twice_does_not_duplicate(tmp_path: Path) -> None:
    s = _settings(tmp_path)
    load_all(s)
    once = _fingerprint(s.db_path)
    load_all(s)
    twice = _fingerprint(s.db_path)
    assert once == twice
    assert once[0] == 5215 + 6380  # both cuts, overlap kept twice in raw (one row per extract x respondent)
    assert once[1] == once[0]  # primary key holds


def test_load_order_does_not_matter(tmp_path: Path) -> None:
    s1 = _settings(tmp_path / "ab")
    load_all(s1, ["cut_a_2016_2018", "cut_b_2018_2021"])
    s2 = _settings(tmp_path / "ba")
    load_all(s2, ["cut_b_2018_2021", "cut_a_2016_2018"])
    assert _fingerprint(s1.db_path) == _fingerprint(s2.db_path)


def test_overlap_rows_are_identical_across_cuts(tmp_path: Path) -> None:
    s = _settings(tmp_path)
    load_all(s)
    conn = duckdb.connect(str(s.db_path), read_only=True)
    try:
        n_overlap, n_differ = conn.execute(
            """
            with a as (select year, id_, record from raw.extract_rows where extract_name = 'cut_a_2016_2018'),
                 b as (select year, id_, record from raw.extract_rows where extract_name = 'cut_b_2018_2021')
            select count(*),
                   -- cut B carries one extra key (prayer); compare the shared keys only
                   sum(case when json_merge_patch(a.record, '{"prayer": null}') <> json_merge_patch(b.record, '{"prayer": null}') then 1 else 0 end)
            from a join b using (year, id_)
            """
        ).fetchone()
    finally:
        conn.close()
    assert n_overlap == 2348
    assert n_differ == 0


def test_every_run_is_recorded(tmp_path: Path) -> None:
    s = _settings(tmp_path)
    load_all(s)
    load_all(s)
    conn = duckdb.connect(str(s.db_path), read_only=True)
    try:
        runs = conn.execute("select extract_name, status, rows_loaded from raw.load_runs order by started_at").fetchall()
        unexpected = conn.execute(
            "select unexpected_columns from raw.load_runs where extract_name = 'cut_b_2018_2021' limit 1"
        ).fetchone()[0]
    finally:
        conn.close()
    assert len(runs) == 4
    assert all(status == "success" for _, status, _ in runs)
    assert json.loads(unexpected) == ["prayer"]


# --- bad input -----------------------------------------------------------------------------


def _write_extract(path: Path, data: dict, codes: dict | None = None) -> None:
    path.write_text(json.dumps({"data": data, "variables": {}, "codes": codes or {}}))


def test_python_repr_file_is_rejected(tmp_path: Path) -> None:
    bad = tmp_path / "GSS.json"
    bad.write_text("{'data': [{'year': '2016', 'id_': 1}]}")  # what the Explorer's GSS.json looks like
    with pytest.raises(ValidationError, match="not valid JSON"):
        parse_extract_file(bad)


def test_ragged_columns_are_rejected(tmp_path: Path) -> None:
    f = tmp_path / "x.json"
    _write_extract(f, {"year": ["2016", "2016"], "id_": [1]})
    with pytest.raises(ValidationError, match="unequal lengths"):
        parse_extract_file(f)


def test_duplicate_key_is_rejected() -> None:
    rows = [{"year": "2016", "id_": 1, "sex": "MALE"}, {"year": "2016", "id_": 1, "sex": "FEMALE"}]
    with pytest.raises(ValidationError, match="duplicate"):
        validate_rows("t", rows, [2016], ["year", "id_", "sex"])


def test_undeclared_year_is_rejected() -> None:
    rows = [{"year": "2014", "id_": 1}]
    with pytest.raises(ValidationError, match="year 2014"):
        validate_rows("t", rows, [2016, 2018], ["year", "id_"])


def test_missing_key_column_is_rejected() -> None:
    with pytest.raises(ValidationError, match="id_"):
        validate_rows("t", [{"year": "2016", "sex": "MALE"}], [2016], ["year", "id_", "sex"])


def test_nested_value_is_rejected() -> None:
    rows = [{"year": "2016", "id_": 1, "sex": ["MALE"]}]
    with pytest.raises(ValidationError, match="non-scalar"):
        validate_rows("t", rows, [2016], ["year", "id_", "sex"])


def test_unexpected_column_is_a_warning_not_an_error() -> None:
    rows = [{"year": "2016", "id_": 1, "sex": "MALE", "bonus": "x"}]
    report = validate_rows("t", rows, [2016], ["year", "id_", "sex"])
    assert report.unexpected_columns == ["bonus"]
    assert any("unexpected columns" in w for w in report.warnings)


def test_failed_load_leaves_previous_rows_and_records_failure(tmp_path: Path) -> None:
    """A bad re-delivery of an extract must not wipe the good rows already loaded."""
    s = _settings(tmp_path)
    load_all(s, ["cut_a_2016_2018"])
    before = _fingerprint(s.db_path)

    bad_dir = tmp_path / "raw"
    bad_dir.mkdir()
    (bad_dir / "cut_a_2016_2018").mkdir()
    _write_extract(
        bad_dir / "cut_a_2016_2018" / "post_processing_output.json",
        {"year": ["2016", "2016"], "id_": [1, 1]},  # duplicate key
    )
    conn = connect(s.db_path)
    try:
        with pytest.raises(ValidationError):
            load_extract(
                conn,
                {"extract_name": "cut_a_2016_2018", "file": "cut_a_2016_2018/post_processing_output.json", "years": [2016]},
                bad_dir,
                ["year", "id_"],
                logging.getLogger("gss.test"),
            )
        statuses = conn.execute(
            "select status from raw.load_runs where extract_name = 'cut_a_2016_2018' order by started_at"
        ).fetchall()
    finally:
        conn.close()
    assert _fingerprint(s.db_path) == before
    assert [s_[0] for s_ in statuses] == ["success", "failed"]
