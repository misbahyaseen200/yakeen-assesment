-- Q3. For each education level, which industry is most common among working respondents?
--
-- "Working" = wrkstat codes 1-3 (full time, part time, with a job but temporarily absent).
-- Industry is reported at two levels: the NAICS sector roll-up (seed_gss__indus10_sectors),
-- which is the headline, and the most common detailed Census industry code, which is shown for
-- transparency because at 271 categories the detailed winner is often a small plurality.

with respondents as (

    select * from {{ ref('fct_respondents') }}

),

sectors as (

    select * from {{ ref('seed_gss__indus10_sectors') }}

),

working as (

    select
        respondents.degree_label,
        respondents.degree_code,
        respondents.indus10_label,
        sectors.sector_name
    from respondents
    left join sectors
        on respondents.indus10_code between sectors.code_from and sectors.code_to
    where
        respondents.wrkstat_group = 'Working'
        and respondents.indus10_status = 'answer'
        and respondents.degree_status = 'answer'

),

sector_counts as (

    select
        degree_label,
        degree_code,
        sector_name,
        count(*) as n_in_sector,
        sum(count(*)) over (partition by degree_label) as n_working_with_industry,
        row_number() over (partition by degree_label order by count(*) desc, sector_name) as sector_rank
    from working
    group by degree_label, degree_code, sector_name

),

detailed_counts as (

    select
        degree_label,
        indus10_label,
        count(*) as n_in_industry,
        row_number() over (partition by degree_label order by count(*) desc, indus10_label) as industry_rank
    from working
    group by degree_label, indus10_label

)

select
    sector_counts.degree_label as education_level,
    sector_counts.n_working_with_industry,
    sector_counts.sector_name as most_common_sector,
    sector_counts.n_in_sector,
    round(sector_counts.n_in_sector / sector_counts.n_working_with_industry, 3) as share_in_sector,
    detailed_counts.indus10_label as most_common_detailed_industry,
    detailed_counts.n_in_industry
from sector_counts
inner join detailed_counts
    on
        sector_counts.degree_label = detailed_counts.degree_label
        and detailed_counts.industry_rank = 1
where sector_counts.sector_rank = 1
order by sector_counts.degree_code
