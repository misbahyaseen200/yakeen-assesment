# q2_afterlife_belief_by_year

Q2. What share of respondents believe in life after death, by survey year, with the number
    not asked shown alongside?

postlife was not fielded in 2021, so that year shows n_not_asked = all respondents and a null
share, never 0%. share_believe is among those who answered yes/no; "don't know" (about 9% in
2016/2018) is reported separately because dropping it silently would overstate certainty.

Source: `dbt/analyses/q2_afterlife_belief_by_year.sql`. Rows: 3.

| year | n_respondents | n_not_asked | n_answered | n_dont_know | n_no_answer | n_believe | share_believe | share_believe_weighted |
|---|---|---|---|---|---|---|---|---|
| 2016 | 2867 | 0 | 2588 | 271 | 8 | 2089 | 0.807 | 0.798 |
| 2018 | 2348 | 0 | 2123 | 216 | 9 | 1720 | 0.81 | 0.806 |
| 2021 | 4032 | 4032 | 0 | 0 | 0 | 0 | null | null |
