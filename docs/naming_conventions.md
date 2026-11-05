# Naming conventions

Applied across the loader, the DuckDB schemas, the dbt project and the analytical SQL.
Everything is lowercase `snake_case`; no quoting is ever needed.

## Schemas (DuckDB) and dbt folders

| layer | schema | dbt folder | materialization | prefix |
|---|---|---|---|---|
| raw (loader-owned) | `raw` | declared as a dbt **source** `gss_raw` | n/a | tables named `<entity>` plainly: `extract_rows`, `extract_codes`, `load_runs` |
| staging | `staging` | `models/staging/gss/` | view | `stg_gss__<entity>` |
| intermediate | `intermediate` | `models/intermediate/` | table | `int_gss__<entity>` |
| marts | `marts` | `models/marts/` | table | `fct_<entity>` (facts), `dim_<entity>` (dimensions) |
| seeds | `metadata` | `seeds/` | seed | `seed_gss__<entity>` |
| analyses | n/a | `analyses/` | n/a | `q<N>_<topic>` for the brief's questions; `audit_<topic>` for audits; `plan_<topic>` for query-plan experiments |

The double underscore separates the **source system** (`gss`) from the entity, following the
dbt style guide. One source system today; the convention makes a second (`pew`, `census`) obvious.

## Models and entities

- Entity names are plural nouns for row collections (`responses`, `respondents`, `variables`).
- Staging models mirror a raw table one-to-one; they never join.
- Intermediate models are named for what they produce, not how (`int_gss__responses_classified`).
- One model per file; file name = model name.

## Columns

| kind | rule | examples |
|---|---|---|
| GSS variable | keep the official GSS mnemonic verbatim in lowercase | `wrkstat`, `relig16`, `wtssps` |
| derived from a GSS variable | mnemonic + suffix | `wrkstat_code`, `wrkstat_label`, `wrkstat_status` |
| surrogate / natural keys | `<entity>_key` | `respondent_key` |
| generic typed value columns in long tables | `value_<aspect>` | `value_code`, `value_label`, `value_status`, `value_numeric` |
| booleans | `is_` / `has_` prefix, never nullable in marts | `is_working`, `has_answer` |
| timestamps | `_at`, UTC | `loaded_at`, `started_at` |
| counts | `n_<thing>` | `n_respondents`, `n_asked` |
| shares / rates | `share_<thing>` (0..1, never percent) | `share_believe` |
| weighted versions | `_weighted` suffix | `n_weighted`, `share_believe_weighted` |
| source bookkeeping | `source_` prefix | `source_extract`, `source_file_sha256` |

Suffix vocabulary is closed: `_code`, `_label`, `_status`, `_group`, `_numeric`, `_key`, `_at`,
`_weighted`. `value_status` values are the closed set
`answer | did_not_apply | dont_know | no_answer | not_asked_in_year | uncodable | unmapped`.

## Seeds

`seed_gss__<entity>.csv`, header row required, UTF-8, LF line endings, no quoting unless a
field contains a comma. Column types are declared in `seeds/_seeds.yml` so that codes are
integers and labels are text regardless of inference.

## Tests

- Generic tests live in the model's `.yml` next to it (`_<folder>__models.yml`).
- Singular tests are `tests/assert_<expectation_in_words>.sql` and must fail with rows that
  explain themselves (they select the offending keys and a `reason` column).
- Custom generic tests are `tests/generic/test_<name>.sql` and used as `<name>:` in yml.

## Sources

One source per upstream system: `sources.yml` declares `gss_raw` with `schema: raw`; tables
keep their raw names. Freshness is not configured (the data is static by design).

## Python

Modules under `source/pipeline/`, `snake_case` files, one responsibility each
(`load_extracts.py`, `validate.py`, `run.py`). Config via environment variables prefixed
`GSS_`. Log events are JSON objects with `event`, `extract`, `level`, `ts` keys.

## Analytical SQL style

- Keywords lowercase, one clause per line, leading commas not used, 4-space indents.
- CTEs instead of subqueries; the final `select` is a plain projection from the last CTE.
- Every aggregate reports its denominator (`n_respondents` or `n_asked`) beside the rate.
- No `select *` outside staging.
