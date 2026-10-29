# Income and Affluence

Model group `income`: 8 predictor(s). Regression runs select this group with `--groups income`. See [how to read these pages](README.md).

| Variable | Name | Source | Role |
|---|---|---|---|
| Hispanic per capita income | `HISPPERCAPINCOME` | ACS | predictor |
| Hispanic poverty rate | `HISPPOVERTY` | ACS | predictor |
| Hispanic SNAP receipt | `HISPSNAP` | ACS | predictor |
| Hispanic owner-occupied housing | `HISPOWNEROCC` | ACS | predictor |
| Hispanic crowded housing | `HISPCROWDING` | ACS | predictor |
| Hispanic broadband access | `HISPBROADBAND` | ACS | predictor |
| Hispanic computer without broadband | `HISPCOMPUTERNOBROADBAND` | ACS | predictor |
| Hispanic no computer | `HISPNOCOMPUTER` | ACS | predictor |

## Variables

### Hispanic per capita income

| | |
|---|---|
| Variable name | `HISPPERCAPINCOME` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Per capita income, Hispanic population (2020 dollars)

**How it is calculated.**

Taken directly from Per capita income in the past 12 months in 2020 inflation adjusted dollars — `B19301I_001E`, ACS table B19301I: Per capita income in the past 12 months (in 2020 inflation-adjusted dollars) (Hispanic or Latino).

### Hispanic poverty rate

| | |
|---|---|
| Variable name | `HISPPOVERTY` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Income in the past 12 months below the poverty level

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** Income in the past 12 months below poverty level — `B17001I_002E`, ACS table B17001I: Poverty status in the past 12 months by sex by age (Hispanic or Latino)

**Bottom (denominator):** Total — `B17001I_001E`, ACS table B17001I: Poverty status in the past 12 months by sex by age (Hispanic or Latino)

Left blank if any input is missing or the bottom number is zero.

### Hispanic SNAP receipt

| | |
|---|---|
| Variable name | `HISPSNAP` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Received SNAP/Food Stamps in the past 12 months

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** Household received food stamps SNAP in the past 12 months — `B22005I_002E`, ACS table B22005I: Receipt of food stamps/SNAP in the past 12 months by race of householder (Hispanic or Latino)

**Bottom (denominator):** Total — `B22005I_001E`, ACS table B22005I: Receipt of food stamps/SNAP in the past 12 months by race of householder (Hispanic or Latino)

Left blank if any input is missing or the bottom number is zero.

### Hispanic owner-occupied housing

| | |
|---|---|
| Variable name | `HISPOWNEROCC` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Owner-occupied (renter-occupied is the exact complement)

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** Owner occupied — `B25003I_002E`, ACS table B25003I: Tenure (Hispanic or Latino householder)

**Bottom (denominator):** Total — `B25003I_001E`, ACS table B25003I: Tenure (Hispanic or Latino householder)

Left blank if any input is missing or the bottom number is zero.

### Hispanic crowded housing

| | |
|---|---|
| Variable name | `HISPCROWDING` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Crowded housing: 1.01 or more occupants per room

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** Occupants per room 1 01 or more — `B25014I_003E`, ACS table B25014I: Occupants per room (Hispanic or Latino householder)

**Bottom (denominator):** Total — `B25014I_001E`, ACS table B25014I: Occupants per room (Hispanic or Latino householder)

Left blank if any input is missing or the bottom number is zero.

### Hispanic broadband access

| | |
|---|---|
| Variable name | `HISPBROADBAND` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Has a computer with a broadband internet subscription

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** Has a computer with a broadband internet subscription — `B28009I_004E`, ACS table B28009I: Presence of a computer and type of internet subscription in household (Hispanic or Latino)

**Bottom (denominator):** Total — `B28009I_001E`, ACS table B28009I: Presence of a computer and type of internet subscription in household (Hispanic or Latino)

Left blank if any input is missing or the bottom number is zero.

### Hispanic computer without broadband

| | |
|---|---|
| Variable name | `HISPCOMPUTERNOBROADBAND` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Has a computer but no broadband (dial-up only, or no subscription)

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** the sum of

- Has a computer with dial up internet subscription alone — `B28009I_003E`, ACS table B28009I: Presence of a computer and type of internet subscription in household (Hispanic or Latino)
- Has a computer without an internet subscription — `B28009I_005E`, ACS table B28009I: Presence of a computer and type of internet subscription in household (Hispanic or Latino)

**Bottom (denominator):** Total — `B28009I_001E`, ACS table B28009I: Presence of a computer and type of internet subscription in household (Hispanic or Latino)

Left blank if any input is missing or the bottom number is zero.

### Hispanic no computer

| | |
|---|---|
| Variable name | `HISPNOCOMPUTER` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** No computer in the household

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** No computer — `B28009I_006E`, ACS table B28009I: Presence of a computer and type of internet subscription in household (Hispanic or Latino)

**Bottom (denominator):** Total — `B28009I_001E`, ACS table B28009I: Presence of a computer and type of internet subscription in household (Hispanic or Latino)

Left blank if any input is missing or the bottom number is zero.
