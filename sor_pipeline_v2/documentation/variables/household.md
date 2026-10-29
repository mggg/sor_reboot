# Household Structure (Age, Marriage, Sex)

Model group `household`: 11 predictor(s). Regression runs select this group with `--groups household`. See [how to read these pages](README.md).

| Variable | Name | Source | Role |
|---|---|---|---|
| Hispanic median age | `HISPMEDAGE` | ACS | predictor |
| Hispanic under 18 | `HISPUNDER18` | ACS | predictor |
| Hispanic 18 to 34 | `HISP18TO34` | ACS | predictor |
| Hispanic 35 to 64 | `HISP35TO64` | ACS | predictor |
| Hispanic 65 and over | `HISP65PLUS` | ACS | predictor |
| Hispanic youth dependency ratio | `HISPYOUTHDEP` | ACS | predictor |
| Hispanic married-couple households | `HISPHHMARRIED` | ACS | predictor |
| Hispanic male householder, no spouse | `HISPHHMALENOSPOUSE` | ACS | predictor |
| Hispanic female householder, no spouse | `HISPHHFEMALENOSPOUSE` | ACS | predictor |
| Hispanic householders living alone | `HISPHHALONE` | ACS | predictor |
| Married-couple share of all households | `HHMARRIEDALL` | ACS | predictor |

## Variables

### Hispanic median age

| | |
|---|---|
| Variable name | `HISPMEDAGE` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Median age of the Hispanic population

**How it is calculated.**

Taken directly from Median age — `B01002I_001E`, ACS table B01002I: Median age by sex (Hispanic or Latino).

### Hispanic under 18

| | |
|---|---|
| Variable name | `HISPUNDER18` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Under 18 years

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** the sum of

- Male under 5 years — `B01001I_003E`, ACS table B01001I: Sex by age (Hispanic or Latino)
- Male 5 to 9 years — `B01001I_004E`, ACS table B01001I: Sex by age (Hispanic or Latino)
- Male 10 to 14 years — `B01001I_005E`, ACS table B01001I: Sex by age (Hispanic or Latino)
- Male 15 to 17 years — `B01001I_006E`, ACS table B01001I: Sex by age (Hispanic or Latino)
- Female under 5 years — `B01001I_018E`, ACS table B01001I: Sex by age (Hispanic or Latino)
- Female 5 to 9 years — `B01001I_019E`, ACS table B01001I: Sex by age (Hispanic or Latino)
- Female 10 to 14 years — `B01001I_020E`, ACS table B01001I: Sex by age (Hispanic or Latino)
- Female 15 to 17 years — `B01001I_021E`, ACS table B01001I: Sex by age (Hispanic or Latino)

**Bottom (denominator):** Total — `B01001I_001E`, ACS table B01001I: Sex by age (Hispanic or Latino)

Left blank if any input is missing or the bottom number is zero.

### Hispanic 18 to 34

| | |
|---|---|
| Variable name | `HISP18TO34` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** 18 to 34 years

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** the sum of

- Male 18 and 19 years — `B01001I_007E`, ACS table B01001I: Sex by age (Hispanic or Latino)
- Male 20 to 24 years — `B01001I_008E`, ACS table B01001I: Sex by age (Hispanic or Latino)
- Male 25 to 29 years — `B01001I_009E`, ACS table B01001I: Sex by age (Hispanic or Latino)
- Male 30 to 34 years — `B01001I_010E`, ACS table B01001I: Sex by age (Hispanic or Latino)
- Female 18 and 19 years — `B01001I_022E`, ACS table B01001I: Sex by age (Hispanic or Latino)
- Female 20 to 24 years — `B01001I_023E`, ACS table B01001I: Sex by age (Hispanic or Latino)
- Female 25 to 29 years — `B01001I_024E`, ACS table B01001I: Sex by age (Hispanic or Latino)
- Female 30 to 34 years — `B01001I_025E`, ACS table B01001I: Sex by age (Hispanic or Latino)

**Bottom (denominator):** Total — `B01001I_001E`, ACS table B01001I: Sex by age (Hispanic or Latino)

Left blank if any input is missing or the bottom number is zero.

### Hispanic 35 to 64

| | |
|---|---|
| Variable name | `HISP35TO64` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** 35 to 64 years

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** the sum of

- Male 35 to 44 years — `B01001I_011E`, ACS table B01001I: Sex by age (Hispanic or Latino)
- Male 45 to 54 years — `B01001I_012E`, ACS table B01001I: Sex by age (Hispanic or Latino)
- Male 55 to 64 years — `B01001I_013E`, ACS table B01001I: Sex by age (Hispanic or Latino)
- Female 35 to 44 years — `B01001I_026E`, ACS table B01001I: Sex by age (Hispanic or Latino)
- Female 45 to 54 years — `B01001I_027E`, ACS table B01001I: Sex by age (Hispanic or Latino)
- Female 55 to 64 years — `B01001I_028E`, ACS table B01001I: Sex by age (Hispanic or Latino)

**Bottom (denominator):** Total — `B01001I_001E`, ACS table B01001I: Sex by age (Hispanic or Latino)

Left blank if any input is missing or the bottom number is zero.

### Hispanic 65 and over

| | |
|---|---|
| Variable name | `HISP65PLUS` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** 65 years and over

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** the sum of

- Male 65 to 74 years — `B01001I_014E`, ACS table B01001I: Sex by age (Hispanic or Latino)
- Male 75 to 84 years — `B01001I_015E`, ACS table B01001I: Sex by age (Hispanic or Latino)
- Male 85 years and over — `B01001I_016E`, ACS table B01001I: Sex by age (Hispanic or Latino)
- Female 65 to 74 years — `B01001I_029E`, ACS table B01001I: Sex by age (Hispanic or Latino)
- Female 75 to 84 years — `B01001I_030E`, ACS table B01001I: Sex by age (Hispanic or Latino)
- Female 85 years and over — `B01001I_031E`, ACS table B01001I: Sex by age (Hispanic or Latino)

**Bottom (denominator):** Total — `B01001I_001E`, ACS table B01001I: Sex by age (Hispanic or Latino)

Left blank if any input is missing or the bottom number is zero.

### Hispanic youth dependency ratio

| | |
|---|---|
| Variable name | `HISPYOUTHDEP` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Youth dependency ratio: Hispanic children (under 18) per Hispanic working-age adult (18 to 64)

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** the sum of

- Male under 5 years — `B01001I_003E`, ACS table B01001I: Sex by age (Hispanic or Latino)
- Male 5 to 9 years — `B01001I_004E`, ACS table B01001I: Sex by age (Hispanic or Latino)
- Male 10 to 14 years — `B01001I_005E`, ACS table B01001I: Sex by age (Hispanic or Latino)
- Male 15 to 17 years — `B01001I_006E`, ACS table B01001I: Sex by age (Hispanic or Latino)
- Female under 5 years — `B01001I_018E`, ACS table B01001I: Sex by age (Hispanic or Latino)
- Female 5 to 9 years — `B01001I_019E`, ACS table B01001I: Sex by age (Hispanic or Latino)
- Female 10 to 14 years — `B01001I_020E`, ACS table B01001I: Sex by age (Hispanic or Latino)
- Female 15 to 17 years — `B01001I_021E`, ACS table B01001I: Sex by age (Hispanic or Latino)

**Bottom (denominator):** Hispanic working age, the sum of

- Male 18 and 19 years — `B01001I_007E`, ACS table B01001I: Sex by age (Hispanic or Latino)
- Male 20 to 24 years — `B01001I_008E`, ACS table B01001I: Sex by age (Hispanic or Latino)
- Male 25 to 29 years — `B01001I_009E`, ACS table B01001I: Sex by age (Hispanic or Latino)
- Male 30 to 34 years — `B01001I_010E`, ACS table B01001I: Sex by age (Hispanic or Latino)
- Male 35 to 44 years — `B01001I_011E`, ACS table B01001I: Sex by age (Hispanic or Latino)
- Male 45 to 54 years — `B01001I_012E`, ACS table B01001I: Sex by age (Hispanic or Latino)
- Male 55 to 64 years — `B01001I_013E`, ACS table B01001I: Sex by age (Hispanic or Latino)
- Female 18 and 19 years — `B01001I_022E`, ACS table B01001I: Sex by age (Hispanic or Latino)
- Female 20 to 24 years — `B01001I_023E`, ACS table B01001I: Sex by age (Hispanic or Latino)
- Female 25 to 29 years — `B01001I_024E`, ACS table B01001I: Sex by age (Hispanic or Latino)
- Female 30 to 34 years — `B01001I_025E`, ACS table B01001I: Sex by age (Hispanic or Latino)
- Female 35 to 44 years — `B01001I_026E`, ACS table B01001I: Sex by age (Hispanic or Latino)
- Female 45 to 54 years — `B01001I_027E`, ACS table B01001I: Sex by age (Hispanic or Latino)
- Female 55 to 64 years — `B01001I_028E`, ACS table B01001I: Sex by age (Hispanic or Latino)

Left blank if any input is missing or the bottom number is zero.

### Hispanic married-couple households

| | |
|---|---|
| Variable name | `HISPHHMARRIED` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Married-couple family households

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** Family households married couple family — `B11001I_003E`, ACS table B11001I: Household type (including living alone) (Hispanic or Latino)

**Bottom (denominator):** Total — `B11001I_001E`, ACS table B11001I: Household type (including living alone) (Hispanic or Latino)

Left blank if any input is missing or the bottom number is zero.

### Hispanic male householder, no spouse

| | |
|---|---|
| Variable name | `HISPHHMALENOSPOUSE` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Male householder, no spouse present

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** Family households other family male householder no spouse present — `B11001I_005E`, ACS table B11001I: Household type (including living alone) (Hispanic or Latino)

**Bottom (denominator):** Total — `B11001I_001E`, ACS table B11001I: Household type (including living alone) (Hispanic or Latino)

Left blank if any input is missing or the bottom number is zero.

### Hispanic female householder, no spouse

| | |
|---|---|
| Variable name | `HISPHHFEMALENOSPOUSE` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Female householder, no spouse present

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** Family households other family female householder no spouse present — `B11001I_006E`, ACS table B11001I: Household type (including living alone) (Hispanic or Latino)

**Bottom (denominator):** Total — `B11001I_001E`, ACS table B11001I: Household type (including living alone) (Hispanic or Latino)

Left blank if any input is missing or the bottom number is zero.

### Hispanic householders living alone

| | |
|---|---|
| Variable name | `HISPHHALONE` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Householder living alone

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** Nonfamily households householder living alone — `B11001I_008E`, ACS table B11001I: Household type (including living alone) (Hispanic or Latino)

**Bottom (denominator):** Total — `B11001I_001E`, ACS table B11001I: Household type (including living alone) (Hispanic or Latino)

Left blank if any input is missing or the bottom number is zero.

### Married-couple share of all households

| | |
|---|---|
| Variable name | `HHMARRIEDALL` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Married-couple family households as a share of every household in the unit, Hispanic or not -- the counterpart to HISPHHMARRIED, which is computed within Hispanic households

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** Family households married couple family — `B11001_003E`, ACS table B11001: Household type (including living alone)

**Bottom (denominator):** Total — `B11001_001E`, ACS table B11001: Household type (including living alone)

Left blank if any input is missing or the bottom number is zero.
