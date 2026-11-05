# Query plan experiment

Measured on 2026-11-03 with DuckDB 2.0.0 on the committed extracts (11,595 raw rows, 273,065
unpivoted cells, 219,061 classified cells). Timings are the mean of 9 warm executions of the
compiled model SQL; `EXPLAIN ANALYZE` operator times are per-thread and therefore sum to less
than wall-clock. Reproduce with `make pipeline` then `EXPLAIN ANALYZE` on
`dbt/target/compiled/gss_religiosity_media/models/intermediate/int_gss__responses_classified.sql`.

## Which query is the most expensive

From `dbt/target/run_results.json` every model builds in under 30 ms except the two that touch
the long form. Executed in isolation, `int_gss__responses_classified` takes **0.37 s**, an order
of magnitude more than anything else, because it (1) unpivots every JSON record into one row per
variable, (2) collapses the 2018 overlap with a `group by` over respondent x variable, and
(3) joins five seeds. It is also the operation whose cost grows fastest with scale: its input is
respondents x variables (75,700 x 7,000 = 530 M cells for the full cumulative file).

## Baseline plan (staging unpivot as a view, inlined)

```
Summary
Projection  [219,061 rows, 10.0ms]
Projection  [219,061 rows, 0µs]
Projection  [219,061 rows, 10.0ms]
Projection  [219,061 rows, 0µs]
Projection  [219,061 rows, 10.0ms]
Hash Join  [219,061 rows, 0µs]
Hash Join  [219,061 rows, 10.0ms]  [26 rows, 0µs]
Hash Join  [219,061 rows, 0µs]  [72 rows, 0µs]
Hash Join  [219,061 rows, 10.0ms]  [34 rows, 0µs]
Hash Join  [219,061 rows, 10.0ms]
Projection  [375 rows, 0µs]  [219,061 rows, 30.0ms]
Projection  [14 rows, 0µs]  [219,061 rows, 0µs]
Hash Group By  [219,061 rows, 110.0ms]
Projection  [273,065 rows, 0µs]
Projection  [273,065 rows, 0µs]
CTE  [0 rows, 0µs]
Projection  [11,595 rows, 0µs]
Table Scan  [273,065 rows, 120.0ms]
Hash Join  [11,595 rows, 0µs]  [273,065 rows, 70.0ms]
CTE Scan  [11,595 rows, 0µs]  [273,065 rows, 50.0ms]
Inout Function  [296,255 rows, 20.0ms]
Projection  [11,595 rows, 10.0ms]
Hash Group By  [11,595 rows, 0µs]
Projection  [11,595 rows, 0µs]
Projection  [11,595 rows, 0µs]
CTE Scan  [11,595 rows, 0µs]
```

Reading bottom-up: the `unnest(json_keys(record))` lateral becomes an **Inout Function** plus a
**Hash Join back onto the record** (DuckDB's de-correlation of the lateral join, 50 + 70 ms), then
a **Projection** that re-parses the full JSON record once per key (`json_extract_string`,
120 ms on 273 k rows). Only then does the dedupe **Hash Group By** (110 ms) and the seed joins run.
About two thirds of the time is the unpivot, not the survey logic.

## The one change: materialise the staging unpivot as a table

`stg_gss__responses` was a view, so the unpivot was recomputed by each consumer (the
classification model and the singular test `assert_overlap_rows_identical_across_cuts`).
Changing one line, `{{ config(materialized='table') }}`, turns the ten unpivot operators into a
single **Table Scan** and the work is done once per pipeline run instead of once per consumer.

```
Summary
Projection  [219,061 rows, 10.0ms]
Projection  [219,061 rows, 0µs]
Projection  [219,061 rows, 0µs]
Projection  [219,061 rows, 0µs]
Projection  [219,061 rows, 0µs]
Hash Join  [219,061 rows, 0µs]
Hash Join  [219,061 rows, 0µs]  [26 rows, 0µs]
Hash Join  [219,061 rows, 0µs]  [72 rows, 0µs]
Hash Join  [219,061 rows, 0µs]  [34 rows, 0µs]
Hash Join  [219,061 rows, 10.0ms]
Projection  [375 rows, 0µs]  [219,061 rows, 30.0ms]
Projection  [14 rows, 0µs]  [219,061 rows, 0µs]
Hash Group By  [219,061 rows, 130.0ms]
Projection  [273,065 rows, 0µs]
Projection  [273,065 rows, 0µs]
Table Scan  [273,065 rows, 0µs]
```

| measure | before | after |
|---|---|---|
| `int_gss__responses_classified` execution (mean of 9) | 0.367 s | 0.317 s |
| operators below the dedupe group-by | 10 (CTE scan, inout function, hash join, 2 projections, ...) | 1 (table scan) |
| one-off cost of materialising the staging table | - | 0.11 s |
| consumers that re-run the unpivot | 2 | 0 |
| result rows / content | 219,061 | identical (checked row by row) |

Net per pipeline run: roughly 2 x 0.25 s saved for 0.11 s spent, with the dedupe `group by`
(130 ms) now the dominant operator, which is the honest shape of the problem: a long table of
respondents x variables grouped on its key.

## Changes tried and rejected

| variant | outcome | why rejected |
|---|---|---|
| dedupe by semi-joining each respondent to one "canonical" extract, before or after the unpivot (removes the group-by) | 13-15 % faster | **changes results**: 2,348 cells of `prayer` exist only in cut B, and are lost when cut A is canonical for 2018. Correct only if every extract has the same columns, which the schema-drift handling explicitly does not assume. |
| unpivot via `cast(record as map(varchar, varchar))` + `unnest` in the select list | 40 % slower | the JSON-to-MAP cast is more expensive than the delim join it avoids |
| unpivot via the `json_each` table function | 25 % slower | same de-correlated join, plus per-cell `json_extract_string` on the value |
| group by two keys (`respondent_key`, `variable_name`) with `any_value(year)` | within noise | DuckDB hashes the wider key cheaply; not worth the less obvious SQL |

## At full scale

At 530 M cells the ranking of the operators does not change but the remedies do:

1. The unpivot should not happen in SQL at all. The loader would write the long form directly
   (one Parquet file per extract, partitioned by `year`), and staging would be a view over
   Parquet. That removes the JSON parse entirely.
2. The dedupe `group by` becomes the bottleneck; it is avoided by making the overlap a
   property of the load (each `(year, id_)` is owned by exactly one extract in a manifest) and
   enforced by a test, instead of being recomputed on every build.
3. `int_gss__responses_classified` and `fct_responses` become **incremental** on `year` (or on
   `source_extract`): a new extract adds its partitions; nothing older is reprocessed.
4. The seed joins are on small dimension tables and stay hash joins; no change needed.

To demonstrate the difference at scale without the full file, the same experiment can be
re-run on the extracts replicated 50x with synthetic `id_` offsets (about 600 k respondents);
the unpivot and group-by times scale linearly and the materialisation saving becomes seconds.
