# audit_overlap_between_cuts

Overlap audit: respondents per cut, in both, distinct overall, overlap as a share of each cut,
and proof that the marts count each respondent once (fct_respondents rows = distinct keys).

Source: `dbt/analyses/audit_overlap_between_cuts.sql`. Rows: 1.

| n_cut_a | n_cut_b | n_in_both | n_distinct_respondents | overlap_share_of_cut_a | overlap_share_of_cut_b | n_raw_rows | n_fct_respondents_rows | n_fct_respondents_keys | n_flagged_in_both | each_respondent_counted_once |
|---|---|---|---|---|---|---|---|---|---|---|
| 5215 | 6380 | 2348 | 9247 | 0.45 | 0.368 | 11595 | 9247 | 9247 | 2348 | True |
