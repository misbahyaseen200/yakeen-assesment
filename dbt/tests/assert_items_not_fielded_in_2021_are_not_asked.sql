-- postlife and reliten were not fielded in the 2021 wave. Every 2021 respondent must carry
-- value_status = 'not_asked_in_year' for both, so a Q2 result can never show 2021 as 0% belief.

select
    variable_name,
    value_status,
    count(*) as n_rows,
    'expected not_asked_in_year for every 2021 respondent' as reason
from {{ ref('fct_responses') }}
where year = 2021
    and variable_name in ('postlife', 'reliten')
    and value_status <> 'not_asked_in_year'
group by variable_name, value_status
