-- The 2018 respondents arrive in both cuts. Collapsing them to one row is only legitimate if
-- both copies carry the same value for every variable. Any row returned here is a conflict.

with responses as (

    select * from {{ ref('stg_gss__responses') }}

),

conflicts as (

    select
        respondent_key,
        variable_name,
        count(distinct raw_value) as n_distinct_values,
        list(raw_value order by source_extract) as values_by_extract,
        'same respondent has different values in the two cuts' as reason
    from responses
    group by respondent_key, variable_name
    having count(distinct raw_value) > 1

)

select * from conflicts
