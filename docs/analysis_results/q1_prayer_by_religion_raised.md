# q1_prayer_by_religion_raised

Q1. How is prayer frequency distributed among respondents, by the religion they were raised in?

Universe: all three years; respondents with a genuine answer to both pray and relig16.
relig16 is grouped into families (seed_gss__answer_groups) because 13 raw categories include
several with fewer than 40 respondents. Shares are row-wise (within each family).
share_* are unweighted; share_daily_weighted uses wtssps to show the weighting effect.

Source: `dbt/analyses/q1_prayer_by_religion_raised.sql`. Rows: 8.

| religion_raised_in | n_respondents | share_several_times_a_day | share_once_a_day | share_several_times_a_week | share_once_a_week | share_less_than_weekly | share_never | share_daily | share_daily_weighted | n_excluded_missing_pray_or_relig16 |
|---|---|---|---|---|---|---|---|---|---|---|
| Protestant | 4589 | 0.359 | 0.246 | 0.119 | 0.046 | 0.102 | 0.126 | 0.606 | 0.595 | 196 |
| Catholic | 2928 | 0.247 | 0.262 | 0.119 | 0.066 | 0.132 | 0.175 | 0.509 | 0.502 | 196 |
| None | 975 | 0.17 | 0.15 | 0.107 | 0.047 | 0.11 | 0.416 | 0.32 | 0.286 | 196 |
| Jewish | 182 | 0.099 | 0.115 | 0.071 | 0.066 | 0.198 | 0.451 | 0.214 | 0.212 | 196 |
| Other Christian | 133 | 0.286 | 0.173 | 0.12 | 0.038 | 0.165 | 0.218 | 0.459 | 0.479 | 196 |
| Eastern religions | 111 | 0.144 | 0.261 | 0.081 | 0.072 | 0.207 | 0.234 | 0.405 | 0.341 | 196 |
| Other | 95 | 0.2 | 0.211 | 0.126 | 0.095 | 0.158 | 0.211 | 0.411 | 0.405 | 196 |
| Muslim | 38 | 0.658 | 0.105 | 0.053 | 0.053 | 0.026 | 0.105 | 0.763 | 0.775 | 196 |
