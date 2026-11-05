-- Analyst-facing catalogue of the modelled variables: what each is, where it is valid, and how
-- many codes it has. Built from the seeds only, so it documents intent, not just observed data.

with variables as (

    select * from {{ ref('seed_gss__variables') }}

),

variable_years as (

    select * from {{ ref('seed_gss__variable_years') }}

),

code_labels as (

    select * from {{ ref('seed_gss__code_labels') }}

),

coverage_by_variable as (

    select
        variable_name,
        list_sort(list(year) filter (where coverage = 'full')) as years_full_sample,
        list_sort(list(year) filter (where coverage = 'ballot')) as years_ballot_limited,
        list_sort(list(year) filter (where coverage = 'subsample')) as years_subsample,
        list_sort(list(year) filter (where coverage = 'none')) as years_not_asked
    from variable_years
    group by variable_name

),

codes_by_variable as (

    select
        variable_name,
        count(*) as n_substantive_codes
    from code_labels
    group by variable_name

),

final as (

    select
        variables.variable_name,
        variables.variable_label,
        variables.value_type,
        variables.topic,
        variables.brief_question,
        variables.universe,
        variables.notes,
        coverage_by_variable.years_full_sample,
        coverage_by_variable.years_ballot_limited,
        coverage_by_variable.years_subsample,
        coverage_by_variable.years_not_asked,
        coalesce(codes_by_variable.n_substantive_codes, 0) as n_substantive_codes
    from variables
    left join coverage_by_variable
        on variables.variable_name = coverage_by_variable.variable_name
    left join codes_by_variable
        on variables.variable_name = codes_by_variable.variable_name
    where variables.is_modelled

)

select * from final
