-- One row per distinct respondent. The 2018 respondents arrive in both cuts; here they are
-- collapsed to one row and we remember which extracts carried them. Whether the two copies
-- were identical is asserted downstream (tests/assert_overlap_rows_identical_across_cuts.sql).

with extract_rows as (

    select * from {{ ref('stg_gss__extract_rows') }}

),

collapsed as (

    select
        respondent_key,
        year,
        id_,
        list_sort(list(source_extract)) as source_extracts,
        count(*) as n_source_extracts,
        count(*) > 1 as is_in_both_cuts,
        max(loaded_at) as last_loaded_at
    from extract_rows
    group by respondent_key, year, id_

)

select * from collapsed
