-- The survey logic, once, in long form: one row per respondent x variable.
--
--  1. collapse the overlap (2018 appears in both cuts) to one row per respondent x variable
--  2. look the exported label up in the seeds to recover the numeric code
--  3. classify every cell into exactly one value_status, trusting the variable-year validity
--     metadata for "not asked in year" over the source's own reserved code
--  4. parse counts and weights, and attach optional coarse groupings
--
-- Nothing here names a variable; adding one means adding seed rows.

with responses as (

    select * from {{ ref('stg_gss__responses') }}

),

variables as (

    select * from {{ ref('seed_gss__variables') }}

),

code_labels as (

    select * from {{ ref('seed_gss__code_labels') }}

),

reserved_codes as (

    select * from {{ ref('seed_gss__reserved_codes') }}

),

variable_years as (

    select * from {{ ref('seed_gss__variable_years') }}

),

answer_groups as (

    select * from {{ ref('seed_gss__answer_groups') }}

),

collapsed as (

    -- min() is deterministic; the test asserting both copies are identical makes it exact.
    select
        respondent_key,
        year,
        id_,
        variable_name,
        min(raw_value) as raw_value,
        list_sort(list(source_extract)) as source_extracts
    from responses
    group by respondent_key, year, id_, variable_name

),

looked_up as (

    select
        collapsed.respondent_key,
        collapsed.year,
        collapsed.id_,
        collapsed.variable_name,
        collapsed.raw_value,
        collapsed.source_extracts,
        variables.value_type,
        variables.is_modelled,
        variable_years.coverage,
        variable_years.ballots as coverage_ballots,
        reserved_codes.code as source_reserved_code,
        reserved_codes.value_status as reserved_value_status,
        reserved_codes.missing_detail as reserved_missing_detail,
        code_labels.code as answer_code,
        answer_groups.group_label,
        answer_groups.group_order,
        -- counts arrive as '47', '0 hours', '89 or older': the leading integer is the value
        case
            when variables.value_type = 'count' and reserved_codes.code is null
                then try_cast(regexp_extract(collapsed.raw_value, '^(\d+)', 1) as integer)
        end as parsed_count,
        case
            when variables.value_type = 'weight'
                then try_cast(collapsed.raw_value as double)
        end as parsed_weight
    from collapsed
    left join variables
        on collapsed.variable_name = variables.variable_name
    left join variable_years
        on
            collapsed.variable_name = variable_years.variable_name
            and collapsed.year = variable_years.year
    left join reserved_codes
        on collapsed.raw_value = reserved_codes.code_label
    left join code_labels
        on
            collapsed.variable_name = code_labels.variable_name
            and collapsed.raw_value = code_labels.code_label
    left join answer_groups
        on
            code_labels.variable_name = answer_groups.variable_name
            and code_labels.code = answer_groups.code

),

classified as (

    select
        respondent_key,
        year,
        id_,
        variable_name,
        value_type,
        is_modelled,
        coverage,
        coverage_ballots,
        raw_value,
        source_extracts,
        source_reserved_code,
        case
            when coverage = 'none' then 'not_asked_in_year'
            when reserved_value_status is not null then reserved_value_status
            when value_type = 'categorical' and answer_code is not null then 'answer'
            when value_type = 'count' and parsed_count is not null then 'answer'
            when value_type = 'weight' and parsed_weight is not null then 'answer'
            else 'unmapped'
        end as value_status,
        case
            when coverage = 'none' and coalesce(source_reserved_code, 0) <> -70
                then 'not_fielded_per_metadata'
            else reserved_missing_detail
        end as missing_detail,
        answer_code,
        parsed_count,
        parsed_weight,
        group_label,
        group_order
    from looked_up

),

final as (

    select
        respondent_key,
        year,
        id_,
        variable_name,
        value_type,
        is_modelled,
        coverage,
        coverage_ballots,
        value_status,
        missing_detail,
        case
            when value_status = 'answer' then coalesce(answer_code, parsed_count)
        end as value_code,
        case
            when value_status = 'answer' and value_type in ('categorical', 'count') then raw_value
        end as value_label,
        case
            when value_status = 'answer' then coalesce(parsed_weight, cast(parsed_count as double))
        end as value_numeric,
        case
            when value_status = 'answer' then coalesce(group_label, raw_value)
        end as value_group,
        case
            when value_status = 'answer' then coalesce(group_order, answer_code, parsed_count)
        end as value_group_order,
        raw_value,
        source_reserved_code,
        source_extracts
    from classified

)

select * from final
