# q5_ever_worked_among_not_working

Q5. Among respondents who are not currently working, what share have ever worked for 12
    months or more?

evwork is asked only of respondents who are retired, in school, keeping house or "other"
(wrkstat 5-8). The unemployed (wrkstat 4) are also "not currently working" but are NOT asked,
so they are shown as a separate row with n_not_asked rather than folded into the denominator.

Source: `dbt/analyses/q5_ever_worked_among_not_working.sql`. Rows: 8.

| year | wrkstat_group | n_respondents | n_not_asked | n_answered | n_dont_know_or_no_answer | n_ever_worked_12_months | share_ever_worked | share_ever_worked_weighted |
|---|---|---|---|---|---|---|---|---|
| 2016 | Not in labour force | 1023 | 0 | 1023 | 0 | 933 | 0.912 | 0.892 |
| 2016 | Unemployed | 118 | 118 | 0 | 0 | 0 | null | null |
| 2018 | Not in labour force | 816 | 0 | 816 | 0 | 739 | 0.906 | 0.861 |
| 2018 | Unemployed | 84 | 84 | 0 | 0 | 0 | null | null |
| 2021 | Not in labour force | 1514 | 0 | 1513 | 1 | 1434 | 0.948 | 0.892 |
| 2021 | Unemployed | 265 | 265 | 0 | 0 | 0 | null | null |
| null | Not in labour force | 3353 | 0 | 3352 | 1 | 3106 | 0.927 | 0.884 |
| null | Unemployed | 467 | 467 | 0 | 0 | 0 | null | null |
