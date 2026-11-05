# q4_tv_hours_vs_job_satisfaction

Q4. Is time spent watching TV related to job satisfaction? Group sizes beside every average.

Universe: respondents with a genuine answer to both tvhours (ballots a and b only) and satjob
(asked of those who work or ever worked). The intersection is roughly a third of each year.
This is a descriptive cross-tab, not a causal claim; the mode change in 2021 is a caveat for
pooling years, so a per-year breakdown is included.

Source: `dbt/analyses/q4_tv_hours_vs_job_satisfaction.sql`. Rows: 16.

| period_label | job_satisfaction | satjob_code | n_respondents | mean_tvhours | mean_tvhours_weighted | median_tvhours | share_4_plus_hours |
|---|---|---|---|---|---|---|---|
| 2016 | Very satisfied | 1 | 508 | 2.62 | 2.52 | 2 | 0.211 |
| 2016 | Moderately satisfied | 2 | 394 | 2.52 | 2.29 | 2 | 0.216 |
| 2016 | A little dissatisfied | 3 | 110 | 2.89 | 2.74 | 2 | 0.3 |
| 2016 | Very dissatisfied | 4 | 39 | 2.33 | 2.41 | 2 | 0.205 |
| 2018 | Very satisfied | 1 | 554 | 2.51 | 2.54 | 2 | 0.213 |
| 2018 | Moderately satisfied | 2 | 438 | 2.65 | 2.56 | 2 | 0.242 |
| 2018 | A little dissatisfied | 3 | 120 | 2.73 | 2.24 | 2 | 0.242 |
| 2018 | Very dissatisfied | 4 | 48 | 3.08 | 2.73 | 3 | 0.375 |
| 2021 | Very satisfied | 1 | 777 | 3.15 | 3.12 | 2 | 0.3 |
| 2021 | Moderately satisfied | 2 | 762 | 2.95 | 3.04 | 2 | 0.273 |
| 2021 | A little dissatisfied | 3 | 215 | 2.92 | 3.11 | 2 | 0.284 |
| 2021 | Very dissatisfied | 4 | 78 | 3.71 | 3.69 | 2 | 0.321 |
| all years | Very satisfied | 1 | 1839 | 2.81 | 2.78 | 2 | 0.249 |
| all years | Moderately satisfied | 2 | 1594 | 2.76 | 2.74 | 2 | 0.25 |
| all years | A little dissatisfied | 3 | 445 | 2.86 | 2.79 | 2 | 0.276 |
| all years | Very dissatisfied | 4 | 165 | 3.2 | 3.17 | 2 | 0.309 |
