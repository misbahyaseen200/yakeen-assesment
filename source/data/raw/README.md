# Raw GSS extracts (as received, never modified)

Source: NORC General Social Survey, downloaded from the GSS Data Explorer
(https://gssdataexplorer.norc.org) on 2026-11-03. Full citation in the repository README.

| folder | Explorer extract name | case selection | records |
|---|---|---|---|
| `cut_a_2016_2018/` | `gss_cut_a_2016_2018` | `year` in (2016, 2018) | 5,215 |
| `cut_b_2018_2021/` | `gss_cut_b_2018_2021` | `year` in (2018, 2021) | 6,380 |

Each folder holds exactly what the Explorer's zip contained (`batch_0.zip/result/*`):

- `post_processing_output.json` - valid JSON, column-oriented. **This is the file the loader reads.**
- `GSS.json` - row-oriented copy, but written as a Python `repr` (single quotes), so it is not parseable JSON. Kept for fidelity; see `docs/data_profile.md`.
- `GSS.dat` - fixed-width numeric codes, no header.
- `GSS.xlsx` - `Data`, `Variables`, `Codes` sheets.
- `xml.ddi3` - DDI 3.1 codebook (structurally broken: all variables share one id).

Variables requested (25): id_, ballot, year, inttech, wwwhr, evwork, news, wrkstat, indus10, satjob,
postlife, relig16, reliten, degree, relig, attend, sex, region, tvhours, age, pray, relitenv, relitennv,
wtssps, wtssnrps. Cut B additionally contains `prayer`, left in the cart by mistake (documented, not modelled).

Integrity: `shasum -a 256 -c MANIFEST.sha256` from this folder (or `make verify-raw`).

The original download archives are not committed (they only wrap the files above); their hashes, for provenance:

```
859d037405eee87f50eca5be39bc13adeada3b405f675e7d228c1f5a2cf93ff3  gss_cut_a_2016_2018.zip
65d99cb13888ac4c2b7924a950caf85ac7549db487ee59a2a55b3411fdd8ec55  gss_cut_b_2018_2021.zip
```
Nothing in this folder is ever edited; all transformation happens downstream in the loader and dbt.
