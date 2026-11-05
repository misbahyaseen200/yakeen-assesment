"""Load the raw GSS extracts into the ``raw`` schema of DuckDB.

Guarantees
----------
* Raw is preserved: every source row is stored as the original JSON object, untouched,
  alongside the key columns needed to address it. No value is cleaned here.
* Idempotent: an extract is loaded inside one transaction that deletes the extract's
  previous rows and reinserts them. Running twice, or loading the cuts in either order,
  leaves ``raw.extract_rows`` identical (see source/tests/test_loader.py).
* Evidence: each attempt writes a row to ``raw.load_runs`` with the file hash, counts,
  validation findings and the outcome, and emits JSON-line logs.

Usage
-----
    python -m source.pipeline.load_extracts --all
    python -m source.pipeline.load_extracts --extract cut_b_2018_2021 --extract cut_a_2016_2018
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import duckdb

from source.pipeline.config import Settings
from source.pipeline.logging_utils import configure_logging, log
from source.pipeline.validate import ValidationError, parse_extract_file, validate_rows

RAW_DDL = """
create schema if not exists raw;

create table if not exists raw.extract_rows (
    extract_name        varchar not null,
    year                integer not null,
    id_                 integer not null,
    row_number          integer not null,   -- 0-based position in the source file
    record              json    not null,   -- the source row, exactly as received
    source_file         varchar not null,
    source_file_sha256  varchar not null,
    load_run_id         varchar not null,
    loaded_at           timestamp not null,
    primary key (extract_name, year, id_)
);

create table if not exists raw.extract_variables (
    extract_name        varchar not null,
    variable_name       varchar not null,
    variable_label      varchar,
    variable_position   integer,
    load_run_id         varchar not null,
    primary key (extract_name, variable_name)
);

create table if not exists raw.extract_codes (
    extract_name        varchar not null,
    variable_name       varchar not null,
    code                integer not null,
    code_label          varchar,
    load_run_id         varchar not null,
    primary key (extract_name, variable_name, code)
);

create table if not exists raw.load_runs (
    load_run_id         varchar primary key,
    extract_name        varchar not null,
    source_file         varchar not null,
    source_file_sha256  varchar,
    started_at          timestamp not null,
    finished_at         timestamp,
    status              varchar not null,   -- 'success' | 'failed'
    rows_read           integer,
    rows_loaded         integer,
    unexpected_columns  json,
    validation          json,
    error               varchar
);
"""


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_manifest(path: Path) -> dict[str, Any]:
    manifest = json.loads(path.read_text())
    names = [e["extract_name"] for e in manifest["extracts"]]
    if len(names) != len(set(names)):
        raise ValueError(f"duplicate extract names in {path}")
    return manifest


def connect(db_path: Path) -> duckdb.DuckDBPyConnection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = duckdb.connect(str(db_path))
    conn.execute(RAW_DDL)
    return conn


def _record_run(conn: duckdb.DuckDBPyConnection, **fields: Any) -> None:
    """Write the load_runs row in its own transaction so it survives a rolled-back load."""
    cols = list(fields)
    conn.execute(
        f"insert or replace into raw.load_runs ({', '.join(cols)}) values ({', '.join('?' for _ in cols)})",
        [fields[c] for c in cols],
    )


def load_extract(
    conn: duckdb.DuckDBPyConnection,
    extract: dict[str, Any],
    raw_dir: Path,
    expected_variables: list[str],
    logger: logging.Logger,
) -> dict[str, Any]:
    """Validate and load one extract. Returns the load_runs row as a dict."""
    name = extract["extract_name"]
    path = raw_dir / extract["file"]
    run_id = str(uuid.uuid4())
    started = datetime.now(timezone.utc)
    ctx = {"extract": name, "run_id": run_id, "file": str(path)}
    log(logger, logging.INFO, "load.start", **ctx)

    file_hash: str | None = None
    try:
        if not path.exists():
            raise ValidationError(f"{name}: file not found: {path}")
        file_hash = sha256_of(path)
        parsed = parse_extract_file(path)
        report = validate_rows(
            name,
            parsed.rows,
            expected_years=list(extract["years"]),
            expected_variables=expected_variables,
            expected_rows=extract.get("expected_rows"),
        )
        for w in report.warnings:
            log(logger, logging.WARNING, "load.validation_warning", warning=w, **ctx)

        loaded_at = datetime.now(timezone.utc)
        row_tuples = [
            (
                name,
                int(r["year"]),
                int(r["id_"]),
                i,
                json.dumps(r, ensure_ascii=False),  # original values and types, untouched
                str(path.relative_to(raw_dir)),
                file_hash,
                run_id,
                loaded_at,
            )
            for i, r in enumerate(parsed.rows)
        ]
        var_tuples = [(name, v["name"], v["label"], v["position"], run_id) for v in parsed.variables]
        code_tuples = [(name, c["variable_name"], c["code"], c["label"], run_id) for c in parsed.codes]

        # One transaction: the extract's previous rows vanish and the new ones appear atomically.
        conn.execute("begin transaction")
        try:
            for table in ("extract_rows", "extract_variables", "extract_codes"):
                conn.execute(f"delete from raw.{table} where extract_name = ?", [name])
            conn.executemany(
                "insert into raw.extract_rows values (?, ?, ?, ?, ?, ?, ?, ?, ?)", row_tuples
            )
            conn.executemany("insert into raw.extract_variables values (?, ?, ?, ?, ?)", var_tuples)
            conn.executemany("insert into raw.extract_codes values (?, ?, ?, ?, ?)", code_tuples)
            conn.execute("commit")
        except Exception:
            conn.execute("rollback")
            raise

        rows_loaded = conn.execute(
            "select count(*) from raw.extract_rows where extract_name = ?", [name]
        ).fetchone()[0]
        if rows_loaded != report.rows_read:  # defensive: should be impossible after commit
            raise RuntimeError(f"{name}: loaded {rows_loaded} rows but read {report.rows_read}")

        result = dict(
            load_run_id=run_id,
            extract_name=name,
            source_file=str(path.relative_to(raw_dir)),
            source_file_sha256=file_hash,
            started_at=started,
            finished_at=datetime.now(timezone.utc),
            status="success",
            rows_read=report.rows_read,
            rows_loaded=rows_loaded,
            unexpected_columns=json.dumps(report.unexpected_columns),
            validation=report.to_json(),
            error=None,
        )
        _record_run(conn, **result)
        log(
            logger, logging.INFO, "load.success", rows_read=report.rows_read, rows_loaded=rows_loaded,
            years=report.years_found, unexpected_columns=report.unexpected_columns, sha256=file_hash, **ctx,
        )
        return result

    except Exception as exc:  # validation or database failure: record it, load nothing
        result = dict(
            load_run_id=run_id,
            extract_name=name,
            source_file=str(path.relative_to(raw_dir)) if path.is_relative_to(raw_dir) else str(path),
            source_file_sha256=file_hash,
            started_at=started,
            finished_at=datetime.now(timezone.utc),
            status="failed",
            rows_read=None,
            rows_loaded=None,
            unexpected_columns=None,
            validation=None,
            error=f"{type(exc).__name__}: {exc}",
        )
        _record_run(conn, **result)
        log(logger, logging.ERROR, "load.failed", error=result["error"], **ctx)
        raise


def load_all(
    settings: Settings, extract_names: list[str] | None = None, logger: logging.Logger | None = None
) -> list[dict[str, Any]]:
    logger = logger or configure_logging(settings.log_dir, settings.log_level)
    manifest = read_manifest(settings.extracts_manifest)
    extracts = manifest["extracts"]
    if extract_names:
        by_name = {e["extract_name"]: e for e in extracts}
        unknown = [n for n in extract_names if n not in by_name]
        if unknown:
            raise SystemExit(f"unknown extract(s) {unknown}; known: {list(by_name)}")
        extracts = [by_name[n] for n in extract_names]  # caller's order is honoured

    conn = connect(settings.db_path)
    results = []
    try:
        for extract in extracts:
            results.append(
                load_extract(conn, extract, settings.raw_dir, manifest["expected_variables"], logger)
            )
    finally:
        conn.close()
    return results


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true", help="load every extract in the manifest, in manifest order")
    group.add_argument("--extract", action="append", help="load this extract (repeatable; order is honoured)")
    args = ap.parse_args(argv)

    settings = Settings.from_env()
    try:
        results = load_all(settings, None if args.all else args.extract)
    except ValidationError:
        return 2
    except Exception:
        return 1
    for r in results:
        print(f"{r['extract_name']}: {r['status']} rows_loaded={r['rows_loaded']} run_id={r['load_run_id']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
