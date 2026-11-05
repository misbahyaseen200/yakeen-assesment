-- Q4. Is time spent watching TV related to job satisfaction? Group sizes beside every average.
--
-- Universe: respondents with a genuine answer to both tvhours (ballots a and b only) and satjob
-- (asked of those who work or ever worked). The intersection is roughly a third of each year.
-- This is a descriptive cross-tab, not a causal claim; the mode change in 2021 is a caveat for
-- pooling years, so a per-year breakdown is included.

with respondents as (

    select * from {{ ref('fct_respondents') }}

),

answered as (

    select
        year,
        satjob_label,
        satjob_code,
        tvhours,
        wtssps
    from respondents
    where
        tvhours_status = 'answer'
        and satjob_status = 'answer'

),

overall as (

    select
        'all years' as period_label,
        satjob_label as job_satisfaction,
        satjob_code,
        count(*) as n_respondents,
        round(avg(tvhours), 2) as mean_tvhours,
        round(sum(tvhours * wtssps) / sum(wtssps), 2) as mean_tvhours_weighted,
        quantile_cont(tvhours, 0.5) as median_tvhours,
        round(count(*) filter (where tvhours >= 4) / count(*), 3) as share_4_plus_hours
    from answered
    group by satjob_label, satjob_code

),

by_year as (

    select
        cast(year as varchar) as period_label,
        satjob_label as job_satisfaction,
        satjob_code,
        count(*) as n_respondents,
        round(avg(tvhours), 2) as mean_tvhours,
        round(sum(tvhours * wtssps) / sum(wtssps), 2) as mean_tvhours_weighted,
        quantile_cont(tvhours, 0.5) as median_tvhours,
        round(count(*) filter (where tvhours >= 4) / count(*), 3) as share_4_plus_hours
    from answered
    group by year, satjob_label, satjob_code

)

select * from overall
union all
select * from by_year
order by period_label, satjob_code
