-- evwork ("ever worked as long as one year") is asked only of respondents who are not
-- currently working and not unemployed (wrkstat 5-8). A genuine evwork answer from anyone
-- with wrkstat 1-4 would mean the universe is not what the codebook says.

select
    respondent_key,
    year,
    wrkstat_label,
    evwork_label,
    'evwork answered by a respondent who is working or unemployed' as reason
from {{ ref('fct_respondents') }}
where evwork_status = 'answer'
    and wrkstat_code between 1 and 4
