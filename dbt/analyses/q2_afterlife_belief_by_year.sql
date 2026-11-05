-- Q2. What share of respondents believe in life after death, by survey year, with the number
--     not asked shown alongside?
--
-- postlife was not fielded in 2021, so that year shows n_not_asked = all respondents and a null
-- share, never 0%. share_believe is among those who answered yes/no; "don't know" (about 9% in
-- 2016/2018) is reported separately because dropping it silently would overstate certainty.

with responses as (

    select * from {{ ref('fct_responses') }}

),

respondents as (

    select
        respondent_key,
        wtssps
    from {{ ref('fct_respondents') }}

),

postlife as (

    select
        responses.year,
        responses.value_status,
        responses.value_code,
        respondents.wtssps
    from responses
    inner join respondents
        on responses.respondent_key = respondents.respondent_key
    where responses.variable_name = 'postlife'

),

by_year as (

    select
        year,
        count(*) as n_respondents,
        count(*) filter (where value_status = 'not_asked_in_year') as n_not_asked,
        count(*) filter (where value_status = 'answer') as n_answered,
        count(*) filter (where value_status = 'dont_know') as n_dont_know,
        count(*) filter (where value_status = 'no_answer') as n_no_answer,
        count(*) filter (where value_code = 1) as n_believe,
        round(count(*) filter (where value_code = 1) / nullif(count(*) filter (where value_status = 'answer'), 0), 3) as share_believe,
        round(sum(wtssps) filter (where value_code = 1) / nullif(sum(wtssps) filter (where value_status = 'answer'), 0), 3) as share_believe_weighted
    from postlife
    group by year

)

select *
from by_year
order by year
