# Data profile of the raw GSS extracts

Written on 2026-11-03 after downloading the two extracts and **before any pipeline code**.
All figures come from `source/profile/profile_raw_extracts.py` (standard library only) and the
full generated tables are in [data_profile_tables.md](data_profile_tables.md).

## 1. What was received

Two extracts built in the GSS Data Explorer (recipe in the README), each delivered as a zip
containing five files. They are committed byte-for-byte under `source/data/raw/` with a
SHA-256 manifest.

| file | what it is | usable? |
|---|---|---|
| `post_processing_output.json` | **valid JSON**, column-oriented: `data` (column -> array), `variables` (name, label), `codes` (per variable: code -> label) | yes, this is the file the pipeline reads |
| `GSS.json` | same content, row-oriented, but it is a **Python `repr()` not JSON** (single quotes). `json.loads` fails | no, kept as received; documented as a source defect |
| `GSS.dat` | fixed-width ASCII with numeric codes, no header | cross-check only |
| `GSS.xlsx` | sheets `Data`, `Variables`, `Codes` (670 code rows) | cross-check for the code lists |
| `xml.ddi3` | DDI 3.1 codebook. Every `Variable` element carries the **same id** and references the **same CodeScheme**, so codes cannot be tied to variables | no |

**Values are exported as labels, not codes.** `wrkstat` holds `"Working full time"`, not `1`.
Reserved (missing) codes are exported as `".i:  Inapplicable"`, `".y:  Not available in this year"`
etc. The numeric codes exist only in `codes` (and in `GSS.dat`). The pipeline therefore has to map
labels back to codes using the embedded code lists, and the code lists become the seed metadata.

**Typing is inconsistent.** `year`, `age`, `tvhours`, `wwwhr`, `wtssps` arrive as strings;
`id_` as int; `wtssnrps` as float. Continuous variables carry labelled endpoints that must be
parsed: `age` = `"89 or older"` (top-code), `tvhours` = `"0 hours"` / `"24 hours"`,
`wwwhr` = `"0 hours"` / `"168 hours"`.

**Schema surprise.** Cut B has 26 columns, cut A has 25. The extra column is `prayer`
(attitude to school prayer), which was added to the MyGSS cart by mistake, removed from cut A's
variable list, but still present in the cart when cut B was built. It is not a variable the
project needs. It is kept in the raw data (raw is preserved as received) and treated by the
loader as a documented, tolerated extra column; it is not exposed in the modelled layer.

## 2. Record counts

| cut | years | records | note |
|---|---|---|---|
| cut_a_2016_2018 | 2016, 2018 | 2,867 + 2,348 = **5,215** | |
| cut_b_2018_2021 | 2018, 2021 | 2,348 + 4,032 = **6,380** | |

Overlap audit on the respondent key `(year, id_)`:

| measure | value |
|---|---|
| in both cuts (all of 2018) | 2,348 |
| distinct respondents overall | 9,247 (limit 10,000) |
| overlap as share of cut A / cut B | 45.0% / 36.8% (minimum 5%) |
| duplicate keys inside either cut | 0 |
| overlapping rows that differ between cuts | 0 (identical on all 25 shared columns) |

`id_` restarts at 1 every year, so `id_` alone is not a respondent identifier; `(year, id_)`
is. In 2016 and 2018 `id_` is contiguous 1..n. In 2021 it runs 1..4471 for 4,032 rows, so gaps
exist and contiguity must not be assumed.

Weights: `wtssps` and `wtssnrps` are present for every row, range 0.17 to 8.5, and
`wtssps` sums to exactly the unweighted n within each year (it is normalised to mean 1).

## 3. How special missing-value codes are distinguished from answers

The GSS reserves negative codes for non-answers. Every variable's code list in the extract
carries the same 14 reserved codes; five of them actually occur in these extracts:

| code | label as exported | meaning | occurrences | brief's category |
|---|---|---|---|---|
| -100 | `.i:  Inapplicable` | question did not apply to this respondent: skip pattern (e.g. `evwork` for people currently working) or **respondent was on a ballot that did not carry the item** | 39,221 | did not apply |
| -70 | `.y:  Not available in this year` | variable not fielded in that survey year | 12,096 | not asked that year |
| -99 | `.n:  No answer` | asked, refused or left blank | 814 | no answer |
| -98 | `.d:  Do not Know/Cannot Choose` | asked, could not answer | 762 | don't know |
| -97 | `.s:  Skipped on Web` | asked in the 2021 self-administered web mode and skipped | 395 | treated as a no-answer subtype (occurs only in 2021) |

Rule used to tell them apart from genuine answers: a genuine answer is any value that is not a
reserved label; a reserved label matches `^\.[a-z]:\s`. In the pipeline the mapping is made by
code, not by string pattern, using the seed metadata.

Two things in the source make this harder than the code list suggests:

1. **"Not asked that year" is encoded two different ways.** `postlife` and `reliten` in 2021 are
   `-70 .y` for all 4,032 rows. But `relitenv` and `relitennv`, which exist only in 2021, are
   `-100 .i` (inapplicable) for every 2016 and 2018 row, not `.y`. Relying on the source code
   alone would make 2016/2018 look like "did not apply" for those two variables. The pipeline
   must therefore derive "not asked that year" from **variable-year validity metadata**, with the
   source `.y` code as a consistency check, rather than trust the source code.
2. **Ballot design is expressed as `.i`.** Items on a split ballot are `.i` for respondents on
   the other ballot(s). "Not on this ballot" and "skipped because of an earlier answer" therefore
   look identical in the data. The pipeline keeps `ballot` so the analyst can separate them and
   so ballot-limited rates are computed over the right denominator.

## 4. Share of missing values per variable per year

Share of rows that are not a genuine answer, over distinct respondents (2018 counted once).
Full breakdown by reserved-code family is in tables 5 and 6 of the generated file.

| variable | 2016 | 2018 | 2021 | dominant reason |
|---|---|---|---|---|
| wrkstat | 0.1% | 0.1% | 0.2% | no answer / skipped on web |
| evwork | 64.3% | 65.2% | 62.5% | inapplicable: only asked of those not currently working |
| indus10 | 4.4% | 4.0% | 5.0% | inapplicable (never worked) / no answer |
| age | 0.3% | 0.3% | 8.3% | 2021: 226 inapplicable + 107 no answer |
| degree | 0.3% | 0.0% | 0.6% | |
| sex | 0.0% | 0.0% | 2.3% | 2021: 71 no answer + 19 inapplicable |
| region | 0.0% | 0.0% | 0.0% | |
| relig | 0.7% | 0.9% | 2.0% | no answer |
| attend | 0.6% | 0.7% | 1.7% | don't know; 2021 also 40 inapplicable |
| reliten | 1.0% | 1.4% | **100%** | 2021: not available in this year |
| postlife | 9.7% | 9.6% | **100%** | 2016/18: ~9% "don't know"; 2021: not available in this year |
| pray | 1.0% | 0.6% | 1.9% | no answer |
| relig16 | 0.7% | 0.7% | 2.6% | |
| satjob | 37.9% | 25.9% | 32.2% | inapplicable: asked of those working or who ever worked; in 2016 also ballot-limited (ballot a got about half) |
| news | 34.3% | 33.6% | 33.1% | inapplicable: ballots a and b only |
| tvhours | 34.3% | 33.8% | 33.5% | inapplicable: ballots a and b only |
| wwwhr | 44.6% | 42.0% | 38.8% | inapplicable: ballots a and b, plus a further skip (about 700 rows have tvhours but no wwwhr) |
| inttech | 51.7% | 50.0% | 53.5% | inapplicable: ballot a + half of ballot b in 2016/18; ballot b + part of c in 2021 |
| ballot, wtssps, wtssnrps | 0% | 0% | 0% | |
| relitenv | 100% | 100% | 50.8% | 2016/18: coded inapplicable although the variable did not exist; 2021: one half of a split sample |
| relitennv | 100% | 100% | 52.3% | as above, the other half |
| prayer | absent | 37.4% | 100% | accidental extra column in cut B only |

## 5. Variables only asked in some years or on some ballots

| variable | availability in these extracts | consequence |
|---|---|---|
| postlife | 2016, 2018 full sample; **not fielded in 2021** | Q2 (belief in afterlife by year) can be answered for 2016 and 2018 only. 2021 is reported as "not asked", with its 4,032 respondents counted and shown, never as 0% belief. |
| reliten | 2016, 2018 full sample; **not fielded in 2021** | In 2021 the item was split into `relitenv` (asked of 1,991 + 1,984) and `relitennv` (the complementary half), with different wording. A coalesced `reliten` with a source flag is possible but is a different instrument; it is provided with that flag, and the flag must be reported alongside any 2021 figure. |
| inttech | ballot-limited in all three years (about half the sample); not fielded after 2021 | "Interest in technology" is answerable in all three years, on roughly 1,200 to 1,900 respondents per year. Which ballots carry it changes between 2018 and 2021, so year-to-year comparison must use the ballot-specific denominator. |
| news, tvhours, wwwhr | ballots a and b only, all three years (about two thirds of the sample) | Q4 and Q6 are answerable in every year but on the ballot subset. Ballot assignment is random, so rates are unbiased for the population, but n is a third smaller than the sample. |
| satjob | full sample in 2018 and 2021; in 2016 about half of ballot a did not receive it; asked only of those who work or ever worked | Q4 (TV vs job satisfaction) uses the intersection of ballots a/b (tvhours) and the satjob universe. |
| evwork | all years, but asked **only of respondents not currently working** (retired, in school, keeping house, other). Unemployed and employed respondents are inapplicable | The brief's wording "if working, have they worked over 12 months" is inverted relative to the GSS instrument. Q5 ("among respondents not currently working") is exactly what the data supports. The unemployed (wrkstat 4) are not asked and are shown as "not asked", not pooled with the asked group. |
| relitenv, relitennv | 2021 only | see reliten |
| sex, age | 2021 has materially more missing (web mode) | demographics breakdowns in 2021 lose 2 to 8% of rows |

Everything else (wrkstat, indus10, degree, sex, region, relig, attend, pray, relig16, ballot,
weights) is on the full sample in every extracted year.

## 6. What the pipeline can and cannot honestly answer

| question (Section 1 / 3) | answerable? | on which rows |
|---|---|---|
| Working status; education; industry; religion raised in; prayer frequency | yes, all years | full sample |
| Worked 12+ months (evwork) | yes, but only for people **not currently working** | wrkstat 5 to 8 |
| Job satisfaction | yes, all years | working / ever-worked universe (2016: partially ballot-limited) |
| Life after death | **2016 and 2018 only** | full sample in those years; 2021 reported as not asked |
| Newspaper, TV, web hours | yes, all years | ballots a and b |
| Interest in technology | yes, all years | ballot subset that differs between 2018 and 2021 |
| Strength of affiliation (reliten) | 2016 and 2018 directly; 2021 only via the split variables with a flag | see above |
| Wave-to-wave change (Q6) | yes, three waves: 2016 -> 2018 -> 2021 | ballots a and b; 2021 is a different survey mode (web), which must be stated as a caveat |

The 2021 wave is a mode change (mostly self-administered web instead of in-person). It shows up
in this profile as the `.s Skipped on Web` code, the higher no-answer share for `sex` and `age`,
the `relitenv`/`relitennv` split and the loss of `postlife`. Any 2018 -> 2021 trend has to carry
a mode-effect caveat.
