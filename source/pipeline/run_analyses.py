"""Execute the dbt analyses (the brief's six questions and the overlap audit) and save results.

dbt compiles analyses but does not run them. This step runs `dbt compile`, executes every
compiled analysis against the warehouse and writes each result as a Markdown table under
docs/analysis_results/, so the numbers quoted in the report are reproducible by anyone.

Usage:  python -m source.pipeline.run_analyses [--out docs/analysis_results]
"""

from __future__ import annotations

import argparse
import logging
import os
import subprocess
import sys
from pathlib import Path

import duckdb

from source.pipeline.config import REPO_ROOT, Settings
from source.pipeline.logging_utils import configure_logging, log


def md_table(columns: list[str], rows: list[tuple]) -> str:
    def fmt(v) -> str:
        if v is None:
            return "null"
        if isinstance(v, float):
            return f"{v:.3f}".rstrip("0").rstrip(".") if abs(v) < 1e6 else f"{v:.3g}"
        return str(v)

    head = "| " + " | ".join(columns) + " |"
    sep = "|" + "|".join("---" for _ in columns) + "|"
    body = ["| " + " | ".join(fmt(v) for v in r) + " |" for r in rows]
    return "\n".join([head, sep, *body])


def compile_analyses(settings: Settings, logger: logging.Logger) -> None:
    env = {**os.environ, "GSS_DB_PATH": str(settings.db_path), "DBT_TARGET": settings.dbt_target}
    cmd = ["dbt", "compile", "--profiles-dir", ".", "--select", "resource_type:analysis", "--quiet"]
    log(logger, logging.INFO, "analyses.compile", cmd=" ".join(cmd))
    subprocess.run(cmd, cwd=settings.dbt_dir, env=env, check=True)


def run_analyses(settings: Settings, out_dir: Path, logger: logging.Logger) -> list[Path]:
    compiled_dir = settings.dbt_dir / "target" / "compiled" / "gss_religiosity_media" / "analyses"
    sql_files = sorted(compiled_dir.glob("*.sql"))
    if not sql_files:
        raise SystemExit(f"no compiled analyses found under {compiled_dir}; run dbt compile first")
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    conn = duckdb.connect(str(settings.db_path), read_only=True)
    try:
        for sql_file in sql_files:
            source_sql = (settings.dbt_dir / "analyses" / sql_file.name).read_text()
            header = [line[3:].rstrip() for line in source_sql.splitlines() if line.startswith("--")]
            cur = conn.execute(sql_file.read_text())
            columns = [d[0] for d in cur.description]
            rows = cur.fetchall()
            out = out_dir / (sql_file.stem + ".md")
            out.write_text(
                f"# {sql_file.stem}\n\n"
                + "\n".join(header)
                + f"\n\nSource: `dbt/analyses/{sql_file.name}`. Rows: {len(rows)}.\n\n"
                + md_table(columns, rows)
                + "\n"
            )
            written.append(out)
            log(logger, logging.INFO, "analyses.ran", analysis=sql_file.stem, rows=len(rows), out=str(out))
    finally:
        conn.close()
    return written


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="docs/analysis_results")
    ap.add_argument("--no-compile", action="store_true", help="reuse target/compiled from an earlier dbt run")
    args = ap.parse_args(argv)
    settings = Settings.from_env()
    logger = configure_logging(settings.log_dir, settings.log_level)
    if not args.no_compile:
        compile_analyses(settings, logger)
    out_dir = Path(args.out)
    out_dir = out_dir if out_dir.is_absolute() else REPO_ROOT / out_dir
    for path in run_analyses(settings, out_dir, logger):
        print(path.relative_to(REPO_ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
