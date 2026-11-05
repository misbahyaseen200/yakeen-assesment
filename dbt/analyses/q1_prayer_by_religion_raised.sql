-- Q1. How is prayer frequency distributed among respondents, by the religion they were raised in?
--
-- Universe: all three years; respondents with a genuine answer to both pray and relig16.
-- relig16 is grouped into families (seed_gss__answer_groups) because 13 raw categories include
-- several with fewer than 40 respondents. Shares are row-wise (within each family).
-- share_* are unweighted; share_daily_weighted uses wtssps to show the weighting effect.

with respondents as (

    select * from {{ ref('fct_respondents') }}

),

answered as (

    select
        relig16_group,
        pray_label,
        pray_code,
        wtssps
    from respondents
    where
        pray_status = 'answer'
        and relig16_status = 'answer'

),

by_family as (

    select
        relig16_group as religion_raised_in,
        count(*) as n_respondents,
        round(count(*) filter (where pray_code = 1) / count(*), 3) as share_several_times_a_day,
        round(count(*) filter (where pray_code = 2) / count(*), 3) as share_once_a_day,
        round(count(*) filter (where pray_code = 3) / count(*), 3) as share_several_times_a_week,
        round(count(*) filter (where pray_code = 4) / count(*), 3) as share_once_a_week,
        round(count(*) filter (where pray_code = 5) / count(*), 3) as share_less_than_weekly,
        round(count(*) filter (where pray_code = 6) / count(*), 3) as share_never,
        round(count(*) filter (where pray_code in (1, 2)) / count(*), 3) as share_daily,
        round(sum(wtssps) filter (where pray_code in (1, 2)) / sum(wtssps), 3) as share_daily_weighted
    from answered
    group by relig16_group

),

excluded as (

    select count(*) as n_excluded_missing_pray_or_relig16
    from respondents
    where not (pray_status = 'answer' and relig16_status = 'answer')

)

select
    by_family.*,
    excluded.n_excluded_missing_pray_or_relig16
from by_family
cross join excluded
order by by_family.n_respondents desc
