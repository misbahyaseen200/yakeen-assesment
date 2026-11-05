-- wtssps is normalised to mean 1 within each survey year, so its sum must equal the number of
-- respondents in that year (to rounding). A drift here means rows were lost or duplicated.

select
    year,
    count(*) as n_respondents,
    round(sum(wtssps), 2) as sum_wtssps,
    'sum of wtssps differs from the number of respondents' as reason
from {{ ref('fct_respondents') }}
group by year
having abs(sum(wtssps) - count(*)) > 0.5
