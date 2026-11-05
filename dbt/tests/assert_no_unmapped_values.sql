-- Every cell must classify. An 'unmapped' status means a label the seeds do not know, or a
-- variable missing from seed_gss__variables / seed_gss__variable_years: a schema surprise.

select
    variable_name,
    year,
    raw_value,
    count(*) as n_rows,
    'value could not be mapped to a code or a reserved code' as reason
from {{ ref('int_gss__responses_classified') }}
where value_status = 'unmapped'
group by variable_name, year, raw_value
