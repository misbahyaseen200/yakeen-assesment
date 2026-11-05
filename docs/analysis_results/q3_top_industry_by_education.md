# q3_top_industry_by_education

Q3. For each education level, which industry is most common among working respondents?

"Working" = wrkstat codes 1-3 (full time, part time, with a job but temporarily absent).
Industry is reported at two levels: the NAICS sector roll-up (seed_gss__indus10_sectors),
which is the headline, and the most common detailed Census industry code, which is shown for
transparency because at 271 categories the detailed winner is often a small plurality.

Source: `dbt/analyses/q3_top_industry_by_education.sql`. Rows: 5.

| education_level | n_working_with_industry | most_common_sector | n_in_sector | share_in_sector | most_common_detailed_industry | n_in_industry |
|---|---|---|---|---|---|---|
| Less than high school | 353 | Construction | 49 | 0.139 | Construction | 49 |
| High school | 2267 | Health care and social assistance | 308 | 0.136 | Construction | 183 |
| Associate/junior college | 494 | Health care and social assistance | 115 | 0.233 | Hospitals | 38 |
| Bachelor's | 1354 | Health care and social assistance | 201 | 0.148 | Elementary and secondary schools | 120 |
| Graduate | 866 | Educational services | 256 | 0.296 | Elementary and secondary schools | 141 |
