# Education

Model group `education`: 4 predictor(s). Regression runs select this group with `--groups education`. See [how to read these pages](README.md).

| Variable | Name | Source | Role |
|---|---|---|---|
| Hispanic less than high school | `HISPEDULTHS` | ACS | predictor |
| Hispanic high school graduates | `HISPEDUHS` | ACS | predictor |
| Hispanic some college | `HISPEDUSOMECOLL` | ACS | predictor |
| Hispanic bachelor's or higher | `HISPEDUBAPLUS` | ACS | predictor |

## Variables

### Hispanic less than high school

| | |
|---|---|
| Variable name | `HISPEDULTHS` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Less than a high school diploma

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** the sum of

- Male less than high school diploma — `C15002I_003E`, ACS table C15002I: Sex by educational attainment for the population 25 years and over (Hispanic or Latino)
- Female less than high school diploma — `C15002I_008E`, ACS table C15002I: Sex by educational attainment for the population 25 years and over (Hispanic or Latino)

**Bottom (denominator):** Total — `C15002I_001E`, ACS table C15002I: Sex by educational attainment for the population 25 years and over (Hispanic or Latino)

Left blank if any input is missing or the bottom number is zero.

### Hispanic high school graduates

| | |
|---|---|
| Variable name | `HISPEDUHS` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** High school graduate or equivalency

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** the sum of

- Male high school graduate includes equivalency — `C15002I_004E`, ACS table C15002I: Sex by educational attainment for the population 25 years and over (Hispanic or Latino)
- Female high school graduate includes equivalency — `C15002I_009E`, ACS table C15002I: Sex by educational attainment for the population 25 years and over (Hispanic or Latino)

**Bottom (denominator):** Total — `C15002I_001E`, ACS table C15002I: Sex by educational attainment for the population 25 years and over (Hispanic or Latino)

Left blank if any input is missing or the bottom number is zero.

### Hispanic some college

| | |
|---|---|
| Variable name | `HISPEDUSOMECOLL` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Some college or an associate's degree

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** the sum of

- Male some college or associate s degree — `C15002I_005E`, ACS table C15002I: Sex by educational attainment for the population 25 years and over (Hispanic or Latino)
- Female some college or associate s degree — `C15002I_010E`, ACS table C15002I: Sex by educational attainment for the population 25 years and over (Hispanic or Latino)

**Bottom (denominator):** Total — `C15002I_001E`, ACS table C15002I: Sex by educational attainment for the population 25 years and over (Hispanic or Latino)

Left blank if any input is missing or the bottom number is zero.

### Hispanic bachelor's or higher

| | |
|---|---|
| Variable name | `HISPEDUBAPLUS` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Bachelor's degree or higher

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** the sum of

- Male bachelor s degree or higher — `C15002I_006E`, ACS table C15002I: Sex by educational attainment for the population 25 years and over (Hispanic or Latino)
- Female bachelor s degree or higher — `C15002I_011E`, ACS table C15002I: Sex by educational attainment for the population 25 years and over (Hispanic or Latino)

**Bottom (denominator):** Total — `C15002I_001E`, ACS table C15002I: Sex by educational attainment for the population 25 years and over (Hispanic or Latino)

Left blank if any input is missing or the bottom number is zero.
