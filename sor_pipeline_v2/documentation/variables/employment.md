# Employment and Industry

Model group `employment`: 12 predictor(s). Regression runs select this group with `--groups employment`. See [how to read these pages](README.md).

| Variable | Name | Source | Role |
|---|---|---|---|
| Hispanic management occupations | `HISPOCCMGMT` | ACS | predictor |
| Hispanic service occupations | `HISPOCCSERVICE` | ACS | predictor |
| Hispanic sales and office occupations | `HISPOCCSALESOFFICE` | ACS | predictor |
| Hispanic natural resources and construction occupations | `HISPOCCNATRESCONST` | ACS | predictor |
| Hispanic production and transportation occupations | `HISPOCCPRODTRANS` | ACS | predictor |
| Agriculture employment | `INDAGRICULTURE` | ACS | predictor |
| Construction employment | `INDCONSTRUCTION` | ACS | predictor |
| Manufacturing employment | `INDMANUFACTURING` | ACS | predictor |
| Education and health employment | `INDEDUHEALTH` | ACS | predictor |
| Accommodation and food employment | `INDACCOMFOOD` | ACS | predictor |
| Hispanic labor force participation | `HISPLFP` | ACS | predictor |
| Hispanic unemployment rate | `HISPUNEMPRATE` | ACS | predictor |

## Variables

### Hispanic management occupations

| | |
|---|---|
| Variable name | `HISPOCCMGMT` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Management, business, science, and arts occupations

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** the sum of

- Male management business science and arts occupations — `C24010I_003E`, ACS table C24010I: Sex by occupation for the civilian employed population 16 years and over (Hispanic or Latino)
- Female management business science and arts occupations — `C24010I_009E`, ACS table C24010I: Sex by occupation for the civilian employed population 16 years and over (Hispanic or Latino)

**Bottom (denominator):** Total — `C24010I_001E`, ACS table C24010I: Sex by occupation for the civilian employed population 16 years and over (Hispanic or Latino)

Left blank if any input is missing or the bottom number is zero.

### Hispanic service occupations

| | |
|---|---|
| Variable name | `HISPOCCSERVICE` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Service occupations

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** the sum of

- Male service occupations — `C24010I_004E`, ACS table C24010I: Sex by occupation for the civilian employed population 16 years and over (Hispanic or Latino)
- Female service occupations — `C24010I_010E`, ACS table C24010I: Sex by occupation for the civilian employed population 16 years and over (Hispanic or Latino)

**Bottom (denominator):** Total — `C24010I_001E`, ACS table C24010I: Sex by occupation for the civilian employed population 16 years and over (Hispanic or Latino)

Left blank if any input is missing or the bottom number is zero.

### Hispanic sales and office occupations

| | |
|---|---|
| Variable name | `HISPOCCSALESOFFICE` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Sales and office occupations

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** the sum of

- Male sales and office occupations — `C24010I_005E`, ACS table C24010I: Sex by occupation for the civilian employed population 16 years and over (Hispanic or Latino)
- Female sales and office occupations — `C24010I_011E`, ACS table C24010I: Sex by occupation for the civilian employed population 16 years and over (Hispanic or Latino)

**Bottom (denominator):** Total — `C24010I_001E`, ACS table C24010I: Sex by occupation for the civilian employed population 16 years and over (Hispanic or Latino)

Left blank if any input is missing or the bottom number is zero.

### Hispanic natural resources and construction occupations

| | |
|---|---|
| Variable name | `HISPOCCNATRESCONST` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Natural resources, construction, and maintenance occupations

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** the sum of

- Male natural resources construction and maintenance occupations — `C24010I_006E`, ACS table C24010I: Sex by occupation for the civilian employed population 16 years and over (Hispanic or Latino)
- Female natural resources construction and maintenance occupations — `C24010I_012E`, ACS table C24010I: Sex by occupation for the civilian employed population 16 years and over (Hispanic or Latino)

**Bottom (denominator):** Total — `C24010I_001E`, ACS table C24010I: Sex by occupation for the civilian employed population 16 years and over (Hispanic or Latino)

Left blank if any input is missing or the bottom number is zero.

### Hispanic production and transportation occupations

| | |
|---|---|
| Variable name | `HISPOCCPRODTRANS` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Production, transportation, and material moving occupations

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** the sum of

- Male production transportation and material moving occupations — `C24010I_007E`, ACS table C24010I: Sex by occupation for the civilian employed population 16 years and over (Hispanic or Latino)
- Female production transportation and material moving occupations — `C24010I_013E`, ACS table C24010I: Sex by occupation for the civilian employed population 16 years and over (Hispanic or Latino)

**Bottom (denominator):** Total — `C24010I_001E`, ACS table C24010I: Sex by occupation for the civilian employed population 16 years and over (Hispanic or Latino)

Left blank if any input is missing or the bottom number is zero.

### Agriculture employment

| | |
|---|---|
| Variable name | `INDAGRICULTURE` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Employed in agriculture, forestry, fishing and hunting

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** the sum of

- Male agriculture forestry fishing and hunting — `C24030_004E`, ACS table C24030: Sex by industry for the civilian employed population 16 years and over
- Female agriculture forestry fishing and hunting — `C24030_031E`, ACS table C24030: Sex by industry for the civilian employed population 16 years and over

**Bottom (denominator):** Total — `C24030_001E`, ACS table C24030: Sex by industry for the civilian employed population 16 years and over

Left blank if any input is missing or the bottom number is zero.

### Construction employment

| | |
|---|---|
| Variable name | `INDCONSTRUCTION` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Employed in construction

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** the sum of

- Male construction — `C24030_006E`, ACS table C24030: Sex by industry for the civilian employed population 16 years and over
- Female construction — `C24030_033E`, ACS table C24030: Sex by industry for the civilian employed population 16 years and over

**Bottom (denominator):** Total — `C24030_001E`, ACS table C24030: Sex by industry for the civilian employed population 16 years and over

Left blank if any input is missing or the bottom number is zero.

### Manufacturing employment

| | |
|---|---|
| Variable name | `INDMANUFACTURING` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Employed in manufacturing

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** the sum of

- Male manufacturing — `C24030_007E`, ACS table C24030: Sex by industry for the civilian employed population 16 years and over
- Female manufacturing — `C24030_034E`, ACS table C24030: Sex by industry for the civilian employed population 16 years and over

**Bottom (denominator):** Total — `C24030_001E`, ACS table C24030: Sex by industry for the civilian employed population 16 years and over

Left blank if any input is missing or the bottom number is zero.

### Education and health employment

| | |
|---|---|
| Variable name | `INDEDUHEALTH` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Employed in educational services, health care, and social assistance

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** the sum of

- Male educational services and health care and social assistance — `C24030_021E`, ACS table C24030: Sex by industry for the civilian employed population 16 years and over
- Female educational services and health care and social assistance — `C24030_048E`, ACS table C24030: Sex by industry for the civilian employed population 16 years and over

**Bottom (denominator):** Total — `C24030_001E`, ACS table C24030: Sex by industry for the civilian employed population 16 years and over

Left blank if any input is missing or the bottom number is zero.

### Accommodation and food employment

| | |
|---|---|
| Variable name | `INDACCOMFOOD` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Employed in accommodation and food services

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** the sum of

- Male accommodation and food services — `C24030_026E`, ACS table C24030: Sex by industry for the civilian employed population 16 years and over
- Female accommodation and food services — `C24030_053E`, ACS table C24030: Sex by industry for the civilian employed population 16 years and over

**Bottom (denominator):** Total — `C24030_001E`, ACS table C24030: Sex by industry for the civilian employed population 16 years and over

Left blank if any input is missing or the bottom number is zero.

### Hispanic labor force participation

| | |
|---|---|
| Variable name | `HISPLFP` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** In the labor force (labor force participation rate)

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** Hispanic labor force, the sum of

- Male 16 to 64 years in labor force — `C23002I_004E`, ACS table C23002I: Sex by age by employment status for the population 16 years and over (Hispanic or Latino)
- Male 65 years and over in labor force — `C23002I_011E`, ACS table C23002I: Sex by age by employment status for the population 16 years and over (Hispanic or Latino)
- Female 16 to 64 years in labor force — `C23002I_017E`, ACS table C23002I: Sex by age by employment status for the population 16 years and over (Hispanic or Latino)
- Female 65 years and over in labor force — `C23002I_024E`, ACS table C23002I: Sex by age by employment status for the population 16 years and over (Hispanic or Latino)

**Bottom (denominator):** Total — `C23002I_001E`, ACS table C23002I: Sex by age by employment status for the population 16 years and over (Hispanic or Latino)

Left blank if any input is missing or the bottom number is zero.

### Hispanic unemployment rate

| | |
|---|---|
| Variable name | `HISPUNEMPRATE` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Unemployed as a share of the labor force

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** the sum of

- Male 16 to 64 years in labor force civilian unemployed — `C23002I_008E`, ACS table C23002I: Sex by age by employment status for the population 16 years and over (Hispanic or Latino)
- Male 65 years and over in labor force unemployed — `C23002I_013E`, ACS table C23002I: Sex by age by employment status for the population 16 years and over (Hispanic or Latino)
- Female 16 to 64 years in labor force civilian unemployed — `C23002I_021E`, ACS table C23002I: Sex by age by employment status for the population 16 years and over (Hispanic or Latino)
- Female 65 years and over in labor force unemployed — `C23002I_026E`, ACS table C23002I: Sex by age by employment status for the population 16 years and over (Hispanic or Latino)

**Bottom (denominator):** Hispanic labor force, the sum of

- Male 16 to 64 years in labor force — `C23002I_004E`, ACS table C23002I: Sex by age by employment status for the population 16 years and over (Hispanic or Latino)
- Male 65 years and over in labor force — `C23002I_011E`, ACS table C23002I: Sex by age by employment status for the population 16 years and over (Hispanic or Latino)
- Female 16 to 64 years in labor force — `C23002I_017E`, ACS table C23002I: Sex by age by employment status for the population 16 years and over (Hispanic or Latino)
- Female 65 years and over in labor force — `C23002I_024E`, ACS table C23002I: Sex by age by employment status for the population 16 years and over (Hispanic or Latino)

Left blank if any input is missing or the bottom number is zero.
