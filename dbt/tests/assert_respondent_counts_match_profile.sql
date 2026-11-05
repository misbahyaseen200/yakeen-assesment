-- The data profile (docs/data_profile.md) established the per-year counts of distinct
-- respondents. The marts must reproduce them exactly: 2016 = 2,867; 2018 = 2,348 (once, although
-- it is in both cuts); 2021 = 4,032; total 9,247.

with expected as (

    select * from (values (2016, 2867), (2018, 2348), (2021, 4032)) as t (year, n_expected)

),

actual as (

    select
        year,
        count(*) as n_actual
    from {{ ref('fct_respondents') }}
    group by year

)

select
    expected.year,
    expected.n_expected,
    actual.n_actual,
    'respondent count per year differs from the data profile' as reason
from expected
full outer join actual
    on expected.year = actual.year
where expected.n_expected is distinct from actual.n_actual
