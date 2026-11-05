-- One row per extract x respondent, straight from the raw layer.
-- Only renames, casts and the derived respondent_key; the JSON record is passed through untouched.

with source as (

    select * from {{ source('gss_raw', 'extract_rows') }}

),

renamed as (

    select
        extract_name as source_extract,
        year,
        id_,
        cast(year as varchar) || '-' || cast(id_ as varchar) as respondent_key,
        record,
        row_number as source_row_number,
        source_file,
        source_file_sha256,
        load_run_id,
        loaded_at
    from source

)

select * from renamed
