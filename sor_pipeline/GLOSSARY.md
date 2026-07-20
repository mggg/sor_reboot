# Glossary: pipeline column names

Definitions for the derived columns used throughout `sor_pipeline`. The raw census
variable codes (P1_xxx / P2_xxx) that these are built from are documented separately
in [`../census_glossary/`](../census_glossary/).

Everything here is 2020 Decennial Census PL 94-171 (redistricting) data — that's
what the "PL" in several column names refers to — plus 2020 presidential election
returns.

## Raw base counts (ingest)

Pulled from the census API and renamed to readable names during ingest.

| Column | Meaning |
| --- | --- |
| `TOTALPOP` | Total population of the unit (county or tract) |
| `HISPANIC` | Hispanic or Latino population (any race) |
| `WHITEALONE` | Everyone (Hispanic or not) who marked White and no other race |
| `SORALONE` | Everyone who marked Some Other Race (SOR) and no other race |
| `WHITESOR` | Everyone who marked exactly White + Some Other Race (two races) |
| `WHITEALONEORCOMBO` | Everyone whose race response **includes** White — alone or in any combination (White+SOR, White+Black, three-race combos, …). Official census concept: "White alone or in combination" |
| `NONHISPANIC<X>` | The non-Hispanic portion of each category above |
| `E_20_PRES_DEM`, `E_20_PRES_REP` | 2020 presidential votes, Democratic / Republican. **All zero in Puerto Rico** (no presidential election there) |

## Derived Hispanic race counts (`clean/features.py: add_hispanic_race_counts`)

One repeating pattern, applied to each race category X:

- `H<X>` = Hispanic people whose race response is X = `<X> − NONHISPANIC<X>`
- `H_N_<X>` = Hispanic people whose race response is **not** X = `HISPANIC − H<X>`
  (the complement used as the second column in half-edge pairs)

| Column | Race category X |
| --- | --- |
| `HSOR` / `H_N_SOR` | Some Other Race alone |
| `HWHITE` / `H_N_WHITE` | White alone |
| `HWHITESOR` / `H_N_WHITESOR` | Exactly White + SOR |
| `HWHITEACOMBO` / `H_N_WHITEACOMBO` | White **a**lone or in **combo** — any response including White |

**Overlap warning:** `HSOR`, `HWHITE`, and `HWHITESOR` are mutually exclusive boxes —
each person is in at most one. `HWHITEACOMBO` is **not** a fourth box: it is an
umbrella that contains `HWHITE` and `HWHITESOR` (plus rarer White combos), so
`HWHITEACOMBO ≥ HWHITE + HWHITESOR` everywhere. Don't read the four as parallel
categories in results tables.

## Population shares (`add_race_percentages`)

| Column | Definition |
| --- | --- |
| `Hisp PL Percent` | `HISPANIC / TOTALPOP` |
| `Hisp SOR Alone PL Percent` | Hispanic-SOR-alone count / denominator |
| `Hisp White Alone PL Percent` | Hispanic-White-alone count / denominator |
| `Hisp White SOR PL Percent` | Hispanic-White+SOR count / denominator |
| `Hisp White PL Percent` | Hispanic White-alone-or-combo count / denominator |

The denominator is `TOTALPOP` in the descriptive/national pipeline and `HISPANIC`
for prediction targets (see the `denominator` parameter).

## Ratios and dominant-race indicators

| Column | Definition |
| --- | --- |
| `* _to_Hisp_Ratio` | Each race share divided by `Hisp PL Percent` (race-within-Hispanic) |
| `largest` | Dominant Hispanic race choice per unit: 1 = SOR alone, 2 = White+SOR, 3 = White alone |
| `Most_SOR`, `Most_White_SOR`, `Most_White` | One-hot versions of `largest` (model targets) |
| `NUMBEROFVOTERS` | `E_20_PRES_DEM + E_20_PRES_REP` |

## Cluster-level rates (`analysis/spatial.py: dissolve_clusters`)

Computed after small-population clustering; these feed Moran's I.

| Column | Definition |
| --- | --- |
| `pct_HSOR` | `HSOR / HISPANIC` |
| `pct_HWhiteSOR` | `HWHITESOR / HISPANIC` |
| `pct_HWHITE` | `HWHITE / HISPANIC` |
| `pct_HWHITEACOMBO` | `HWHITEACOMBO / HISPANIC` |
| `pct_HISP` | `HISPANIC / TOTALPOP` |
| `pct_DEM` | `E_20_PRES_DEM / (E_20_PRES_DEM + E_20_PRES_REP + 1)` — the `+1` avoids 0/0, but it also means "no election" (Puerto Rico) shows up as 0.0, not as missing |
| `NONHISPANIC` | `TOTALPOP − HISPANIC` |
| `dem_base` | `E_20_PRES_DEM + E_20_PRES_REP + 1` (denominator for the raw/Empirical-Bayes Moran specs) |

## Display labels (spec lists in `runners/national/run_spatial_analysis.py`)

| Label | Column(s) |
| --- | --- |
| `SORA` | `HSOR` (SOR alone) |
| `WhiteA` | `HWHITE` (White alone) |
| `White + SOR` | `HWHITESOR` |
| `WhiteAorCombo` / `White alone or combo` | `HWHITEACOMBO` — "alone **or** in combination", NOT combos-only |
| `Hispanic` | `HISPANIC` |
| `Democrat` / `Democrat vs Republican` | `E_20_PRES_DEM` (vs `E_20_PRES_REP` / `dem_base`) |
