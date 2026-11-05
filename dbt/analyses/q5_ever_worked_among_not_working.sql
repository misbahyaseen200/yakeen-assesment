-- Q5. Among respondents who are not currently working, what share have ever worked for 12
--     months or more?
--
-- evwork is asked only of respondents who are retired, in school, keeping house or "other"
-- (wrkstat 5-8). The unemployed (wrkstat 4) are also "not currently working" but are NOT asked,
-- so they are shown as a separate row with n_not_asked rather than folded into the denominator.

with respondents as (

    select * from {{ ref('fct_respondents') }}

),

not_working as (

    select
        year,
        wrkstat_group,
        wrkstat_label,
        evwork_status,
        evwork_code,
        wtssps
    from respondents
    where wrkstat_group in ('Unemployed', 'Not in labour force')

),

by_group as (

    select
        year,
        wrkstat_group,
        count(*) as n_respondents,
        count(*) filter (where evwork_status = 'did_not_apply') as n_not_asked,
        count(*) filter (where evwork_status = 'answer') as n_answered,
        count(*) filter (where evwork_status in ('dont_know', 'no_answer')) as n_dont_know_or_no_answer,
        count(*) filter (where evwork_code = 1) as n_ever_worked_12_months,
        round(count(*) filter (where evwork_code = 1) / nullif(count(*) filter (where evwork_status = 'answer'), 0), 3) as share_ever_worked,
        round(sum(wtssps) filter (where evwork_code = 1) / nullif(sum(wtssps) filter (where evwork_status = 'answer'), 0), 3) as share_ever_worked_weighted
    from not_working
    group by year, wrkstat_group

),

all_years as (

    select
        null as year,
        wrkstat_group,
        count(*) as n_respondents,
        count(*) filter (where evwork_status = 'did_not_apply') as n_not_asked,
        count(*) filter (where evwork_status = 'answer') as n_answered,
        count(*) filter (where evwork_status in ('dont_know', 'no_answer')) as n_dont_know_or_no_answer,
        count(*) filter (where evwork_code = 1) as n_ever_worked_12_months,
        round(count(*) filter (where evwork_code = 1) / nullif(count(*) filter (where evwork_status = 'answer'), 0), 3) as share_ever_worked,
        round(sum(wtssps) filter (where evwork_code = 1) / nullif(sum(wtssps) filter (where evwork_status = 'answer'), 0), 3) as share_ever_worked_weighted
    from not_working
    group by wrkstat_group

)

select * from by_group
union all
select * from all_years
order by year nulls last, wrkstat_group
