-- Long fact: one row per respondent x modelled variable. The generic surface for aggregation
-- ("for variable X in year Y, how many answered / did not apply / were not asked").

with classified as (

    select * from {{ ref('int_gss__responses_classified') }}

),

final as (

    select
        respondent_key,
        year,
        id_,
        variable_name,
        value_type,
        coverage,
        value_status,
        missing_detail,
        value_code,
        value_label,
        value_numeric,
        value_group,
        value_group_order,
        source_reserved_code,
        source_extracts
    from classified
    where is_modelled

)

select * from final
