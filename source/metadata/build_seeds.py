"""Generate the code-list seeds for dbt from the extracts' embedded metadata.

The GSS Data Explorer ships, inside every extract, the code -> label list of each requested
variable. This script turns that into two version-controlled CSV seeds:

* ``dbt/seeds/seed_gss__code_labels.csv``   one row per variable x substantive (>= 0) code
* ``dbt/seeds/seed_gss__reserved_codes.csv`` one row per reserved (< 0) code, with the
  missing-value semantics assigned here, once, for every variable

It reads the raw JSON files directly (not the database) so the seeds can be regenerated
without a loaded warehouse, and it refuses to proceed when the extracts disagree with each
other about any code, because that would mean the labels are not stable.

The hand-curated seeds (variables, variable_years, indus10_sectors, answer_groups) are NOT
touched by this script.

Usage:  python -m source.metadata.build_seeds
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

from source.pipeline.config import REPO_ROOT

SEEDS_DIR = REPO_ROOT / "dbt" / "seeds"
MANIFEST = REPO_ROOT / "source" / "data" / "extracts.json"
RAW_DIR = REPO_ROOT / "source" / "data" / "raw"

# Semantics of the reserved codes. value_status is the closed set used throughout the dbt
# layer (see docs/naming_conventions.md); missing_detail keeps the finer source distinction.
RESERVED_SEMANTICS: dict[int, tuple[str, str]] = {
    -100: ("did_not_apply", "inapplicable"),
    -99: ("no_answer", "no_answer"),
    -98: ("dont_know", "dont_know_cannot_choose"),
    -97: ("no_answer", "skipped_on_web"),
    -96: ("uncodable", "variable_specific_reserve"),
    -95: ("uncodable", "uncodable"),
    -94: ("uncodable", "not_imputable"),
    -93: ("no_answer", "missing_birthdate"),
    -90: ("no_answer", "refused"),
    -80: ("not_asked_in_year", "not_available_in_release"),
    -70: ("not_asked_in_year", "not_available_in_year"),
    -60: ("did_not_apply", "no_job"),
    -50: ("did_not_apply", "not_applicable_or_not_imputable"),
    -40: ("no_answer", "dk_na_iap_combined"),
}


def main() -> int:
    manifest = json.loads(MANIFEST.read_text())
    substantive: dict[tuple[str, int], str] = {}
    reserved: dict[int, str] = {}
    conflicts: list[str] = []

    for extract in manifest["extracts"]:
        doc = json.loads((RAW_DIR / extract["file"]).read_text())
        for entry in doc["codes"].values():
            var = entry["variable_name"]
            for code_str, label in entry["CodeLabel"].items():
                code = int(code_str)
                if code < 0:
                    if reserved.setdefault(code, label) != label:
                        conflicts.append(f"reserved {code}: {reserved[code]!r} vs {label!r}")
                    continue
                key = (var, code)
                if substantive.setdefault(key, label) != label:
                    conflicts.append(f"{var} {code}: {substantive[key]!r} vs {label!r}")

    if conflicts:
        print("extracts disagree on code labels; refusing to write seeds:", *conflicts, sep="\n  ")
        return 1
    unknown = sorted(c for c in reserved if c not in RESERVED_SEMANTICS)
    if unknown:
        print(f"reserved codes without semantics in RESERVED_SEMANTICS: {unknown}")
        return 1

    SEEDS_DIR.mkdir(parents=True, exist_ok=True)
    with (SEEDS_DIR / "seed_gss__code_labels.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["variable_name", "code", "code_label"])
        for (var, code), label in sorted(substantive.items()):
            w.writerow([var, code, label])

    with (SEEDS_DIR / "seed_gss__reserved_codes.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["code", "code_label", "value_status", "missing_detail"])
        for code in sorted(reserved, reverse=True):
            status, detail = RESERVED_SEMANTICS[code]
            w.writerow([code, reserved[code], status, detail])

    n_vars = len({v for v, _ in substantive})
    print(f"wrote {len(substantive)} substantive codes for {n_vars} variables and {len(reserved)} reserved codes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
