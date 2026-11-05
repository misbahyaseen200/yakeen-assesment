-- The metadata (seed_gss__variable_years) decides "not asked in year". This test checks the
-- source agrees where it can: a variable marked coverage = 'none' must be entirely reserved
-- codes in the source (either .y -70 or, for relitenv/relitennv, .i -100), never a real answer,
-- and conversely a source .y code must only appear where coverage = 'none'.

with classified as (

    select * from {{ ref('int_gss__responses_classified') }}

),

answers_where_not_fielded as (

    select
        variable_name,
        year,
        count(*) as n_rows,
        'metadata says not fielded but source has a substantive answer' as reason
    from classified
    where
        coverage = 'none'
        and source_reserved_code is null
    group by variable_name, year

),

source_says_not_available_but_metadata_disagrees as (

    select
        variable_name,
        year,
        count(*) as n_rows,
        'source code -70 (.y) but metadata says the variable was fielded' as reason
    from classified
    where
        source_reserved_code = -70
        and coverage <> 'none'
    group by variable_name, year

)

select * from answers_where_not_fielded
union all
select * from source_says_not_available_but_metadata_disagrees
