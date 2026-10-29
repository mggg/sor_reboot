# US Citizenship and Residency Status

Model group `citizenship`: 2 predictor(s) and 1 context variable(s). Regression runs select this group with `--groups citizenship`. See [how to read these pages](README.md).

| Variable | Name | Source | Role |
|---|---|---|---|
| Hispanic adult naturalized citizens | `HISPADULTNATURALIZED` | ACS | predictor |
| Hispanic adult noncitizens | `HISPADULTNONCITIZEN` | ACS | predictor |
| Citizen voting-age population | `VOTINGAGEPOP` | ACS | context |

## Variables

### Hispanic adult naturalized citizens

| | |
|---|---|
| Variable name | `HISPADULTNATURALIZED` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Share of Hispanic adults (18+) who are naturalized U.S. citizens

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** the sum of

- Male 18 years and over foreign born naturalized U.S. citizen — `B05003I_011E`, ACS table B05003I: Sex by age by nativity and citizenship status (Hispanic or Latino)
- Female 18 years and over foreign born naturalized U.S. citizen — `B05003I_022E`, ACS table B05003I: Sex by age by nativity and citizenship status (Hispanic or Latino)

**Bottom (denominator):** Hispanic adults, the sum of

- Male 18 years and over — `B05003I_008E`, ACS table B05003I: Sex by age by nativity and citizenship status (Hispanic or Latino)
- Female 18 years and over — `B05003I_019E`, ACS table B05003I: Sex by age by nativity and citizenship status (Hispanic or Latino)

Left blank if any input is missing or the bottom number is zero.

### Hispanic adult noncitizens

| | |
|---|---|
| Variable name | `HISPADULTNONCITIZEN` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Share of Hispanic adults (18+) who are not U.S. citizens

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** the sum of

- Male 18 years and over foreign born not a U.S. citizen — `B05003I_012E`, ACS table B05003I: Sex by age by nativity and citizenship status (Hispanic or Latino)
- Female 18 years and over foreign born not a U.S. citizen — `B05003I_023E`, ACS table B05003I: Sex by age by nativity and citizenship status (Hispanic or Latino)

**Bottom (denominator):** Hispanic adults, the sum of

- Male 18 years and over — `B05003I_008E`, ACS table B05003I: Sex by age by nativity and citizenship status (Hispanic or Latino)
- Female 18 years and over — `B05003I_019E`, ACS table B05003I: Sex by age by nativity and citizenship status (Hispanic or Latino)

Left blank if any input is missing or the bottom number is zero.

### Citizen voting-age population

| | |
|---|---|
| Variable name | `VOTINGAGEPOP` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Context: kept in the dataset for reference, never a model input |
| Available for | Counties and tracts |

**What it measures.** Citizen voting-age population (citizens 18 years and over)

**How it is calculated.**

Taken directly from Total — `B29001_001E`, ACS table B29001: Citizen, voting-age population by age.
