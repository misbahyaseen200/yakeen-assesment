-- Long form: one row per extract x respondent x variable, unpivoted generically from the JSON
-- record. No variable name is written here, so a new variable in a future extract flows
-- through without touching staging. The key columns (year, id_) are not responses.

with extract_rows as (

    select * from {{ ref('stg_gss__extract_rows') }}

),

unpivoted as (

    select
        extract_rows.source_extract,
        extract_rows.year,
        extract_rows.id_,
        extract_rows.respondent_key,
        record_keys.variable_name,
        json_extract_string(extract_rows.record, '$.' || record_keys.variable_name) as raw_value,
        json_type(extract_rows.record, '$.' || record_keys.variable_name) as raw_json_type
    from extract_rows,
        unnest(json_keys(extract_rows.record)) as record_keys (variable_name)

)

select *
from unpivoted
where variable_name not in ('year', 'id_')
