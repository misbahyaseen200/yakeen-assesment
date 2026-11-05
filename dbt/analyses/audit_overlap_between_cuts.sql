-- Overlap audit: respondents per cut, in both, distinct overall, overlap as a share of each cut,
-- and proof that the marts count each respondent once (fct_respondents rows = distinct keys).

with extract_rows as (

    select * from {{ ref('stg_gss__extract_rows') }}

),

per_cut as (

    select
        count(*) filter (where source_extract = 'cut_a_2016_2018') as n_cut_a,
        count(*) filter (where source_extract = 'cut_b_2018_2021') as n_cut_b,
        count(distinct respondent_key) as n_distinct_respondents,
        count(*) as n_raw_rows
    from extract_rows

),

in_both as (

    select count(*) as n_in_both
    from (
        select respondent_key
        from extract_rows
        group by respondent_key
        having count(distinct source_extract) = 2
    ) as shared_respondents

),

marts as (

    select
        count(*) as n_fct_respondents_rows,
        count(distinct respondent_key) as n_fct_respondents_keys,
        count(*) filter (where is_in_both_cuts) as n_flagged_in_both
    from {{ ref('fct_respondents') }}

)

select
    per_cut.n_cut_a,
    per_cut.n_cut_b,
    in_both.n_in_both,
    per_cut.n_distinct_respondents,
    round(in_both.n_in_both / per_cut.n_cut_a, 3) as overlap_share_of_cut_a,
    round(in_both.n_in_both / per_cut.n_cut_b, 3) as overlap_share_of_cut_b,
    per_cut.n_raw_rows,
    marts.n_fct_respondents_rows,
    marts.n_fct_respondents_keys,
    marts.n_flagged_in_both,
    marts.n_fct_respondents_rows = per_cut.n_distinct_respondents
    and marts.n_fct_respondents_rows = marts.n_fct_respondents_keys as each_respondent_counted_once
from per_cut
cross join in_both
cross join marts
