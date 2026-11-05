"""Pipeline orchestrator: runs the steps in order, stops at the first failure, records evidence.

Steps (in this order, each depends on the previous):
    load         Python loader: validate + load raw extracts (idempotent)
    seed         dbt build (seeds only): load the metadata seeds and run their tests
    build        dbt build     : run models and their tests in dependency order; a failing
                                 test stops everything downstream of that model
    analyses     run the brief's queries and save results under docs/analysis_results/
    docs         dbt docs generate

Why a plain Python runner and not Airflow/Dagster/Prefect: five sequential steps on a 12k-row
dataset that is static by design. A scheduler would add a service, a metadata database and a
UI to babysit, and would not change what runs. The runner still gives what the brief asks for:
explicit ordering, fail-fast, safe re-runs (every step is idempotent), a run manifest and logs.

Usage:
    python -m source.pipeline.run                 # everything
    python -m source.pipeline.run --from build    # resume after fixing a model
    python -m source.pipeline.run --only load     # one step
Exit code is non-zero when any step fails; the failing step is named in the manifest.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

from source.pipeline.config import REPO_ROOT, Settings
from source.pipeline.logging_utils import configure_logging, log

STEPS = ["load", "seed", "build", "analyses", "docs"]


def _dbt(settings: Settings, *args: str) -> list[str]:
    return ["dbt", *args, "--profiles-dir", str(settings.dbt_dir), "--project-dir", str(settings.dbt_dir)]


def step_commands(settings: Settings) -> dict[str, list[str]]:
    py = [sys.executable, "-m"]
    return {
        "load": [*py, "source.pipeline.load_extracts", "--all"],
        "seed": _dbt(settings, "build", "--select", "resource_type:seed"),  # seeds + their tests
        "build": _dbt(settings, "build", "--exclude", "resource_type:seed"),
        "analyses": [*py, "source.pipeline.run_analyses"],
        "docs": _dbt(settings, "docs", "generate"),
    }


def run_step(name: str, cmd: list[str], settings: Settings, run_id: str, logger: logging.Logger) -> dict:
    env = {
        **os.environ,
        "GSS_DB_PATH": str(settings.db_path),
        "DBT_TARGET": settings.dbt_target,
        "GSS_PIPELINE_RUN_ID": run_id,
    }
    started = time.monotonic()
    log(logger, logging.INFO, "step.start", step=name, run_id=run_id, cmd=" ".join(cmd))
    # Child output goes to the terminal; dbt writes its own logs to dbt/logs and run_results.json.
    proc = subprocess.run(cmd, check=False, cwd=REPO_ROOT, env=env)  # exit code handled below
    record = {
        "step": name,
        "status": "success" if proc.returncode == 0 else "failed",
        "exit_code": proc.returncode,
        "duration_s": round(time.monotonic() - started, 2),
    }
    log(logger, logging.INFO if proc.returncode == 0 else logging.ERROR, "step.finish", run_id=run_id, **record)
    return record


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--from", dest="from_step", choices=STEPS, help="start at this step (earlier steps assumed done)")
    ap.add_argument("--only", choices=STEPS, help="run exactly one step")
    args = ap.parse_args(argv)

    settings = Settings.from_env()
    logger = configure_logging(settings.log_dir, settings.log_level)
    run_id = str(uuid.uuid4())
    steps = [args.only] if args.only else STEPS[STEPS.index(args.from_step) :] if args.from_step else STEPS

    manifest = {
        "run_id": run_id,
        "started_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "db_path": str(settings.db_path),
        "dbt_target": settings.dbt_target,
        "steps": [],
        "status": "running",
    }
    commands = step_commands(settings)
    for name in steps:
        record = run_step(name, commands[name], settings, run_id, logger)
        manifest["steps"].append(record)
        if record["status"] != "success":
            manifest["status"] = "failed"
            manifest["failed_step"] = name
            break
    else:
        manifest["status"] = "success"
    manifest["finished_at"] = datetime.now(UTC).isoformat(timespec="seconds")

    settings.log_dir.mkdir(parents=True, exist_ok=True)
    with (settings.log_dir / "pipeline_runs.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(manifest) + "\n")
    Path(settings.log_dir / "last_run.json").write_text(json.dumps(manifest, indent=2) + "\n")

    print(f"\npipeline {manifest['status']} (run_id={run_id})")
    for s in manifest["steps"]:
        print(f"  {s['step']:9s} {s['status']:8s} {s['duration_s']:6.1f}s")
    return 0 if manifest["status"] == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
