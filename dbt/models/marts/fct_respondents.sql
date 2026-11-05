-- Wide fact: one row per respondent, one column set per modelled variable, generated from the
-- variable seed by the respondent_wide_columns macro. Analysts who want "a normal survey table"
-- start here; fct_responses is the long equivalent.

-- depends_on: {{ ref('seed_gss__variables') }} {{ ref('seed_gss__answer_groups') }}
{% set wide_columns = respondent_wide_columns('responses') %}

with respondents as (

    select * from {{ ref('int_gss__respondents') }}

),

responses as (

    select * from {{ ref('fct_responses') }}

),

pivoted as (

    select
        respondents.respondent_key,
        respondents.year,
        respondents.id_,
        respondents.source_extracts,
        respondents.is_in_both_cuts
        {%- for column_expression in wide_columns %}
            ,
            {{ column_expression }}
    
        {%- endfor %}
    from respondents
    left join responses
        on respondents.respondent_key = responses.respondent_key
    group by
        respondents.respondent_key,
        respondents.year,
        respondents.id_,
        respondents.source_extracts,
        respondents.is_in_both_cuts

)

select * from pivoted
