# Language

Model group `language`: 12 predictor(s). Regression runs select this group with `--groups language`. See [how to read these pages](README.md).

| Variable | Name | Source | Role |
|---|---|---|---|
| Hispanic English-only at home | `HISPENGONLY` | ACS | predictor |
| Spanish speakers, English very well | `HISPSPANVERYWELL` | ACS | predictor |
| Spanish speakers, English well | `HISPSPANWELL` | ACS | predictor |
| Spanish speakers, English not well | `HISPSPANNOTWELL` | ACS | predictor |
| Spanish speakers, English not at all | `HISPSPANNOTATALL` | ACS | predictor |
| Hispanic other language at home | `HISPOTHERLANG` | ACS | predictor |
| Native-born Hispanic English-only | `HISPNATIVEENGONLY` | ACS | predictor |
| Native-born Hispanic bilingual, English very well | `HISPNATIVEOTHERVW` | ACS | predictor |
| Native-born Hispanic English less than very well | `HISPNATIVEOTHERLTVW` | ACS | predictor |
| Foreign-born Hispanic English-only | `HISPFBENGONLY` | ACS | predictor |
| Foreign-born Hispanic bilingual, English very well | `HISPFBOTHERVW` | ACS | predictor |
| Foreign-born Hispanic English less than very well | `HISPFBOTHERLTVW` | ACS | predictor |

## Variables

### Hispanic English-only at home

| | |
|---|---|
| Variable name | `HISPENGONLY` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Hispanics who speak only English at home

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** Speak only English — `B16006_002E`, ACS table B16006: Language spoken at home by ability to speak English for the population 5 years and over (Hispanic or Latino)

**Bottom (denominator):** Total — `B16006_001E`, ACS table B16006: Language spoken at home by ability to speak English for the population 5 years and over (Hispanic or Latino)

Left blank if any input is missing or the bottom number is zero.

### Spanish speakers, English very well

| | |
|---|---|
| Variable name | `HISPSPANVERYWELL` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Spanish speakers who report speaking English "very well"

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** Speak Spanish speak English very well — `B16006_004E`, ACS table B16006: Language spoken at home by ability to speak English for the population 5 years and over (Hispanic or Latino)

**Bottom (denominator):** Total — `B16006_001E`, ACS table B16006: Language spoken at home by ability to speak English for the population 5 years and over (Hispanic or Latino)

Left blank if any input is missing or the bottom number is zero.

### Spanish speakers, English well

| | |
|---|---|
| Variable name | `HISPSPANWELL` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Spanish speakers who report speaking English "well"

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** Speak Spanish speak English well — `B16006_005E`, ACS table B16006: Language spoken at home by ability to speak English for the population 5 years and over (Hispanic or Latino)

**Bottom (denominator):** Total — `B16006_001E`, ACS table B16006: Language spoken at home by ability to speak English for the population 5 years and over (Hispanic or Latino)

Left blank if any input is missing or the bottom number is zero.

### Spanish speakers, English not well

| | |
|---|---|
| Variable name | `HISPSPANNOTWELL` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Spanish speakers who report speaking English "not well"

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** Speak Spanish speak English not well — `B16006_006E`, ACS table B16006: Language spoken at home by ability to speak English for the population 5 years and over (Hispanic or Latino)

**Bottom (denominator):** Total — `B16006_001E`, ACS table B16006: Language spoken at home by ability to speak English for the population 5 years and over (Hispanic or Latino)

Left blank if any input is missing or the bottom number is zero.

### Spanish speakers, English not at all

| | |
|---|---|
| Variable name | `HISPSPANNOTATALL` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Spanish speakers who report speaking English "not at all"

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** Speak Spanish speak English not at all — `B16006_007E`, ACS table B16006: Language spoken at home by ability to speak English for the population 5 years and over (Hispanic or Latino)

**Bottom (denominator):** Total — `B16006_001E`, ACS table B16006: Language spoken at home by ability to speak English for the population 5 years and over (Hispanic or Latino)

Left blank if any input is missing or the bottom number is zero.

### Hispanic other language at home

| | |
|---|---|
| Variable name | `HISPOTHERLANG` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Hispanics who speak a language other than English or Spanish at home

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** Speak other language — `B16006_008E`, ACS table B16006: Language spoken at home by ability to speak English for the population 5 years and over (Hispanic or Latino)

**Bottom (denominator):** Total — `B16006_001E`, ACS table B16006: Language spoken at home by ability to speak English for the population 5 years and over (Hispanic or Latino)

Left blank if any input is missing or the bottom number is zero.

### Native-born Hispanic English-only

| | |
|---|---|
| Variable name | `HISPNATIVEENGONLY` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Native-born Hispanics who speak only English at home

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** Native speak only English — `B16005I_003E`, ACS table B16005I: Nativity by language spoken at home by ability to speak English for the population 5 years and over (Hispanic or Latino)

**Bottom (denominator):** Total — `B16005I_001E`, ACS table B16005I: Nativity by language spoken at home by ability to speak English for the population 5 years and over (Hispanic or Latino)

Left blank if any input is missing or the bottom number is zero.

### Native-born Hispanic bilingual, English very well

| | |
|---|---|
| Variable name | `HISPNATIVEOTHERVW` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Native-born Hispanics who speak another language and English "very well"

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** Native speak another language speak English very well — `B16005I_005E`, ACS table B16005I: Nativity by language spoken at home by ability to speak English for the population 5 years and over (Hispanic or Latino)

**Bottom (denominator):** Total — `B16005I_001E`, ACS table B16005I: Nativity by language spoken at home by ability to speak English for the population 5 years and over (Hispanic or Latino)

Left blank if any input is missing or the bottom number is zero.

### Native-born Hispanic English less than very well

| | |
|---|---|
| Variable name | `HISPNATIVEOTHERLTVW` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Native-born Hispanics who speak another language and English less than "very well"

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** Native speak another language speak English less than very well — `B16005I_006E`, ACS table B16005I: Nativity by language spoken at home by ability to speak English for the population 5 years and over (Hispanic or Latino)

**Bottom (denominator):** Total — `B16005I_001E`, ACS table B16005I: Nativity by language spoken at home by ability to speak English for the population 5 years and over (Hispanic or Latino)

Left blank if any input is missing or the bottom number is zero.

### Foreign-born Hispanic English-only

| | |
|---|---|
| Variable name | `HISPFBENGONLY` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Foreign-born Hispanics who speak only English at home

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** Foreign born speak only English — `B16005I_008E`, ACS table B16005I: Nativity by language spoken at home by ability to speak English for the population 5 years and over (Hispanic or Latino)

**Bottom (denominator):** Total — `B16005I_001E`, ACS table B16005I: Nativity by language spoken at home by ability to speak English for the population 5 years and over (Hispanic or Latino)

Left blank if any input is missing or the bottom number is zero.

### Foreign-born Hispanic bilingual, English very well

| | |
|---|---|
| Variable name | `HISPFBOTHERVW` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Foreign-born Hispanics who speak another language and English "very well"

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** Foreign born speak another language speak English very well — `B16005I_010E`, ACS table B16005I: Nativity by language spoken at home by ability to speak English for the population 5 years and over (Hispanic or Latino)

**Bottom (denominator):** Total — `B16005I_001E`, ACS table B16005I: Nativity by language spoken at home by ability to speak English for the population 5 years and over (Hispanic or Latino)

Left blank if any input is missing or the bottom number is zero.

### Foreign-born Hispanic English less than very well

| | |
|---|---|
| Variable name | `HISPFBOTHERLTVW` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Foreign-born Hispanics who speak another language and English less than "very well"

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** Foreign born speak another language speak English less than very well — `B16005I_011E`, ACS table B16005I: Nativity by language spoken at home by ability to speak English for the population 5 years and over (Hispanic or Latino)

**Bottom (denominator):** Total — `B16005I_001E`, ACS table B16005I: Nativity by language spoken at home by ability to speak English for the population 5 years and over (Hispanic or Latino)

Left blank if any input is missing or the bottom number is zero.
