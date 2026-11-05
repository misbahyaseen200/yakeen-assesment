{#
  Generate the column expressions that pivot fct_responses (long) into fct_respondents (wide),
  driven by seed_gss__variables so the wide table grows when the seed grows.

  Per modelled variable (identifiers excluded):
    categorical  -> <var>_label, <var>_code, <var>_status, plus <var>_group when seed_gss__answer_groups defines groups
    count        -> <var>, <var>_status
    weight       -> <var>

  The variable list is read at execution time (run_query), so the macro needs the seed to be
  loaded: `dbt seed` must run before `dbt run` (the pipeline runner enforces this).
#}
{% macro respondent_wide_columns(responses_alias='responses') %}
    {%- set columns = [] -%}
    {%- if execute -%}
        {%- set query -%}
            select
                variables.variable_name,
                variables.value_type,
                exists (
                    select 1 from {{ ref('seed_gss__answer_groups') }} as groups
                    where groups.variable_name = variables.variable_name
                ) as has_groups
            from {{ ref('seed_gss__variables') }} as variables
            where variables.is_modelled and variables.value_type <> 'identifier'
            order by variables.variable_name
        {%- endset -%}
        {%- set rows = run_query(query) -%}
        {%- for row in rows -%}
            {%- set v = row[0] -%}
            {%- set t = row[1] -%}
            {%- set has_groups = row[2] -%}
            {%- if t == 'categorical' -%}
                {%- do columns.append("max(case when " ~ responses_alias ~ ".variable_name = '" ~ v ~ "' then " ~ responses_alias ~ ".value_label end) as " ~ v ~ "_label") -%}
                {%- do columns.append("max(case when " ~ responses_alias ~ ".variable_name = '" ~ v ~ "' then " ~ responses_alias ~ ".value_code end) as " ~ v ~ "_code") -%}
                {%- if has_groups -%}
                {%- do columns.append("max(case when " ~ responses_alias ~ ".variable_name = '" ~ v ~ "' then " ~ responses_alias ~ ".value_group end) as " ~ v ~ "_group") -%}
                {%- endif -%}
                {%- do columns.append("max(case when " ~ responses_alias ~ ".variable_name = '" ~ v ~ "' then " ~ responses_alias ~ ".value_status end) as " ~ v ~ "_status") -%}
            {%- elif t == 'count' -%}
                {%- do columns.append("max(case when " ~ responses_alias ~ ".variable_name = '" ~ v ~ "' then cast(" ~ responses_alias ~ ".value_numeric as integer) end) as " ~ v) -%}
                {%- do columns.append("max(case when " ~ responses_alias ~ ".variable_name = '" ~ v ~ "' then " ~ responses_alias ~ ".value_status end) as " ~ v ~ "_status") -%}
            {%- elif t == 'weight' -%}
                {%- do columns.append("max(case when " ~ responses_alias ~ ".variable_name = '" ~ v ~ "' then " ~ responses_alias ~ ".value_numeric end) as " ~ v) -%}
            {%- endif -%}
        {%- endfor -%}
    {%- endif -%}
    {{ return(columns) }}
{% endmacro %}
