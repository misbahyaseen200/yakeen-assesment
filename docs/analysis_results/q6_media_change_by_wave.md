# q6_media_change_by_wave

Q6. How have newspaper reading and TV viewing changed from one survey wave to the next?

Both items are on ballots a and b only, in every extracted year. Waves: 2016 -> 2018 -> 2021.
Caveat: 2021 switched to a mostly self-administered web mode; part of any 2018 -> 2021 change
can be mode effect rather than behaviour. Weighted shares use wtssps.

Source: `dbt/analyses/q6_media_change_by_wave.sql`. Rows: 3.

| year | n_news_answered | share_read_daily | share_read_daily_weighted | share_never_read | n_tvhours_answered | mean_tvhours | mean_tvhours_weighted | share_tv_4_plus_hours | change_share_read_daily | change_share_never_read | change_mean_tvhours |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2016 | 1885 | 0.211 | 0.209 | 0.365 | 1883 | 3.03 | 2.78 | 0.302 | null | null | null |
| 2018 | 1559 | 0.2 | 0.181 | 0.435 | 1555 | 2.94 | 2.74 | 0.286 | -0.011 | 0.07 | -0.09 |
| 2021 | 2696 | 0.238 | 0.205 | 0.371 | 2683 | 3.46 | 3.38 | 0.378 | 0.038 | -0.064 | 0.52 |
