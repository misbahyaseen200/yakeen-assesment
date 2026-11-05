{#
  Use the schema configured on the model/seed verbatim (staging, intermediate, marts, metadata)
  instead of dbt's default "<target schema>_<custom schema>" concatenation, so the warehouse
  layout matches docs/naming_conventions.md in every target.
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
