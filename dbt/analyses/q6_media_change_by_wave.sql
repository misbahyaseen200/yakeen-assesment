-- Q6. How have newspaper reading and TV viewing changed from one survey wave to the next?
--
-- Both items are on ballots a and b only, in every extracted year. Waves: 2016 -> 2018 -> 2021.
-- Caveat: 2021 switched to a mostly self-administered web mode; part of any 2018 -> 2021 change
-- can be mode effect rather than behaviour. Weighted shares use wtssps.

with respondents as (

    select * from {{ ref('fct_respondents') }}

),

news_by_year as (

    select
        year,
        count(*) as n_news_answered,
        round(count(*) filter (where news_code = 1) / count(*), 3) as share_read_daily,
        round(sum(wtssps) filter (where news_code = 1) / sum(wtssps), 3) as share_read_daily_weighted,
        round(count(*) filter (where news_code = 5) / count(*), 3) as share_never_read
    from respondents
    where news_status = 'answer'
    group by year

),

tv_by_year as (

    select
        year,
        count(*) as n_tvhours_answered,
        round(avg(tvhours), 2) as mean_tvhours,
        round(sum(tvhours * wtssps) / sum(wtssps), 2) as mean_tvhours_weighted,
        round(count(*) filter (where tvhours >= 4) / count(*), 3) as share_tv_4_plus_hours
    from respondents
    where tvhours_status = 'answer'
    group by year

),

joined as (

    select
        news_by_year.year,
        news_by_year.n_news_answered,
        news_by_year.share_read_daily,
        news_by_year.share_read_daily_weighted,
        news_by_year.share_never_read,
        tv_by_year.n_tvhours_answered,
        tv_by_year.mean_tvhours,
        tv_by_year.mean_tvhours_weighted,
        tv_by_year.share_tv_4_plus_hours
    from news_by_year
    inner join tv_by_year
        on news_by_year.year = tv_by_year.year

),

with_change as (

    select
        *,
        round(share_read_daily - lag(share_read_daily) over (order by year), 3) as change_share_read_daily,
        round(share_never_read - lag(share_never_read) over (order by year), 3) as change_share_never_read,
        round(mean_tvhours - lag(mean_tvhours) over (order by year), 2) as change_mean_tvhours
    from joined

)

select *
from with_change
order by year
