# Racial and Ethnic Composition

Model group `racial_ethnic`: 6 predictor(s). Regression runs select this group with `--groups racial_ethnic`. See [how to read these pages](README.md).

| Variable | Name | Source | Role |
|---|---|---|---|
| Non-Hispanic White share | `NONHISPANICWHITESHARE` | ACS | predictor |
| Non-Hispanic Black share | `NONHISPANICBLACKSHARE` | ACS | predictor |
| Non-Hispanic AIAN share | `NONHISPANICAIANSHARE` | ACS | predictor |
| Non-Hispanic Asian share | `NONHISPANICASIANSHARE` | ACS | predictor |
| Non-Hispanic multiracial share | `NONHISPANICMULTISHARE` | ACS | predictor |
| Hispanic share | `HISPSHARE` | ACS | predictor |

## Variables

### Non-Hispanic White share

| | |
|---|---|
| Variable name | `NONHISPANICWHITESHARE` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Non-Hispanic White alone

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** Not Hispanic or Latino white alone — `B03002_003E`, ACS table B03002: Hispanic or Latino origin by race

**Bottom (denominator):** Total — `B03002_001E`, ACS table B03002: Hispanic or Latino origin by race

Left blank if any input is missing or the bottom number is zero.

### Non-Hispanic Black share

| | |
|---|---|
| Variable name | `NONHISPANICBLACKSHARE` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Non-Hispanic Black or African American alone

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** Not Hispanic or Latino black or African American alone — `B03002_004E`, ACS table B03002: Hispanic or Latino origin by race

**Bottom (denominator):** Total — `B03002_001E`, ACS table B03002: Hispanic or Latino origin by race

Left blank if any input is missing or the bottom number is zero.

### Non-Hispanic AIAN share

| | |
|---|---|
| Variable name | `NONHISPANICAIANSHARE` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Non-Hispanic American Indian and Alaska Native alone

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** Not Hispanic or Latino American indian and Alaska Native alone — `B03002_005E`, ACS table B03002: Hispanic or Latino origin by race

**Bottom (denominator):** Total — `B03002_001E`, ACS table B03002: Hispanic or Latino origin by race

Left blank if any input is missing or the bottom number is zero.

### Non-Hispanic Asian share

| | |
|---|---|
| Variable name | `NONHISPANICASIANSHARE` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Non-Hispanic Asian alone

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** Not Hispanic or Latino Asian alone — `B03002_006E`, ACS table B03002: Hispanic or Latino origin by race

**Bottom (denominator):** Total — `B03002_001E`, ACS table B03002: Hispanic or Latino origin by race

Left blank if any input is missing or the bottom number is zero.

### Non-Hispanic multiracial share

| | |
|---|---|
| Variable name | `NONHISPANICMULTISHARE` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Non-Hispanic, two or more races -- the unit's non-Hispanic propensity for multiracial reporting

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** Not Hispanic or Latino two or more races — `B03002_009E`, ACS table B03002: Hispanic or Latino origin by race

**Bottom (denominator):** Total — `B03002_001E`, ACS table B03002: Hispanic or Latino origin by race

Left blank if any input is missing or the bottom number is zero.

### Hispanic share

| | |
|---|---|
| Variable name | `HISPSHARE` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Hispanic or Latino, any race

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** Hispanic or Latino — `B03002_012E`, ACS table B03002: Hispanic or Latino origin by race

**Bottom (denominator):** Total — `B03002_001E`, ACS table B03002: Hispanic or Latino origin by race

Left blank if any input is missing or the bottom number is zero.
