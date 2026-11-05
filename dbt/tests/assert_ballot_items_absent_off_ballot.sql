-- A ballot-limited item must never have a genuine answer from a respondent on a ballot that
-- did not carry it. Ballot letters per variable-year come from seed_gss__variable_years.

with responses as (

    select * from {{ ref('fct_responses') }}

),

respondents as (

    select
        respondent_key,
        lower(right(ballot_label, 1)) as ballot_letter
    from {{ ref('fct_respondents') }}

),

variable_years as (

    select * from {{ ref('seed_gss__variable_years') }}
    where coverage = 'ballot'

),

violations as (

    select
        responses.variable_name,
        responses.year,
        respondents.ballot_letter,
        count(*) as n_rows,
        'answer recorded on a ballot that did not carry the item' as reason
    from responses
    inner join respondents
        on responses.respondent_key = respondents.respondent_key
    inner join variable_years
        on responses.variable_name = variable_years.variable_name
        and responses.year = variable_years.year
    where responses.value_status = 'answer'
        and not list_contains(string_split(variable_years.ballots, ','), respondents.ballot_letter)
    group by responses.variable_name, responses.year, respondents.ballot_letter

)

select * from violations
