# Mobility and Time in the U.S.

Model group `mobility`: 18 predictor(s). Regression runs select this group with `--groups mobility`. See [how to read these pages](README.md).

| Variable | Name | Source | Role |
|---|---|---|---|
| Hispanic adults foreign born | `HISPADULTFB` | ACS | predictor |
| Hispanic children foreign born | `HISPCHILDFB` | ACS | predictor |
| Foreign-born share | `FOREIGNBORNSHARE` | ACS | predictor |
| Born in Puerto Rico | `PRBORNSHARE` | ACS | predictor |
| Foreign born entered 2010 or later | `FBENTERED2010PLUS` | ACS | predictor |
| Foreign born entered 2000-2009 | `FBENTERED2000S` | ACS | predictor |
| Foreign born entered 1990-1999 | `FBENTERED1990S` | ACS | predictor |
| Foreign born entered before 1990 | `FBENTEREDPRE1990` | ACS | predictor |
| Latin American foreign born entered 2010 or later | `LATAMFBENTERED2010PLUS` | ACS | predictor |
| Latin American foreign born entered 2000-2009 | `LATAMFBENTERED2000S` | ACS | predictor |
| Latin American foreign born entered 1990-1999 | `LATAMFBENTERED1990S` | ACS | predictor |
| Latin American foreign born entered before 1990 | `LATAMFBENTEREDPRE1990` | ACS | predictor |
| Hispanic moved within county | `HISPMOVEDWITHINCOUNTY` | ACS | predictor |
| Hispanic moved from another county | `HISPMOVEDDIFFCOUNTY` | ACS | predictor |
| Hispanic moved from another state | `HISPMOVEDDIFFSTATE` | ACS | predictor |
| Hispanic moved from abroad | `HISPMOVEDABROAD` | ACS | predictor |
| Hispanic population growth | `HISPGROWTH` | ACS | predictor |
| Foreign-born population growth | `FBGROWTH` | ACS | predictor |

## Variables

### Hispanic adults foreign born

| | |
|---|---|
| Variable name | `HISPADULTFB` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Share of Hispanic adults (18+) who are foreign born

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** the sum of

- Male 18 years and over foreign born — `B05003I_010E`, ACS table B05003I: Sex by age by nativity and citizenship status (Hispanic or Latino)
- Female 18 years and over foreign born — `B05003I_021E`, ACS table B05003I: Sex by age by nativity and citizenship status (Hispanic or Latino)

**Bottom (denominator):** Hispanic adults, the sum of

- Male 18 years and over — `B05003I_008E`, ACS table B05003I: Sex by age by nativity and citizenship status (Hispanic or Latino)
- Female 18 years and over — `B05003I_019E`, ACS table B05003I: Sex by age by nativity and citizenship status (Hispanic or Latino)

Left blank if any input is missing or the bottom number is zero.

### Hispanic children foreign born

| | |
|---|---|
| Variable name | `HISPCHILDFB` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Share of Hispanic children (under 18) who are foreign born

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** the sum of

- Male under 18 years foreign born — `B05003I_005E`, ACS table B05003I: Sex by age by nativity and citizenship status (Hispanic or Latino)
- Female under 18 years foreign born — `B05003I_016E`, ACS table B05003I: Sex by age by nativity and citizenship status (Hispanic or Latino)

**Bottom (denominator):** Hispanic children, the sum of

- Male under 18 years — `B05003I_003E`, ACS table B05003I: Sex by age by nativity and citizenship status (Hispanic or Latino)
- Female under 18 years — `B05003I_014E`, ACS table B05003I: Sex by age by nativity and citizenship status (Hispanic or Latino)

Left blank if any input is missing or the bottom number is zero.

### Foreign-born share

| | |
|---|---|
| Variable name | `FOREIGNBORNSHARE` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Share of the total population that is foreign born

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** Foreign born — `B05002_013E`, ACS table B05002: Place of birth by nativity and citizenship status

**Bottom (denominator):** Total — `B05002_001E`, ACS table B05002: Place of birth by nativity and citizenship status

Left blank if any input is missing or the bottom number is zero.

### Born in Puerto Rico

| | |
|---|---|
| Variable name | `PRBORNSHARE` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Share of the total population born in Puerto Rico (native-born, so invisible to every foreign-born measure)

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** Native born outside the United States Puerto Rico — `B05002_010E`, ACS table B05002: Place of birth by nativity and citizenship status

**Bottom (denominator):** Total — `B05002_001E`, ACS table B05002: Place of birth by nativity and citizenship status

Left blank if any input is missing or the bottom number is zero.

### Foreign born entered 2010 or later

| | |
|---|---|
| Variable name | `FBENTERED2010PLUS` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Of the foreign born, the share who entered the U.S. in 2010 or later

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** Entered 2010 or later foreign born — `B05005_004E`, ACS table B05005: Period of entry by nativity and citizenship status in the United States

**Bottom (denominator):** Foreign born by entry period, the sum of

- Entered 2010 or later foreign born — `B05005_004E`, ACS table B05005: Period of entry by nativity and citizenship status in the United States
- Entered 2000 to 2009 foreign born — `B05005_009E`, ACS table B05005: Period of entry by nativity and citizenship status in the United States
- Entered 1990 to 1999 foreign born — `B05005_014E`, ACS table B05005: Period of entry by nativity and citizenship status in the United States
- Entered before 1990 foreign born — `B05005_019E`, ACS table B05005: Period of entry by nativity and citizenship status in the United States

Left blank if any input is missing or the bottom number is zero.

### Foreign born entered 2000-2009

| | |
|---|---|
| Variable name | `FBENTERED2000S` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Of the foreign born, the share who entered the U.S. 2000-2009

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** Entered 2000 to 2009 foreign born — `B05005_009E`, ACS table B05005: Period of entry by nativity and citizenship status in the United States

**Bottom (denominator):** Foreign born by entry period, the sum of

- Entered 2010 or later foreign born — `B05005_004E`, ACS table B05005: Period of entry by nativity and citizenship status in the United States
- Entered 2000 to 2009 foreign born — `B05005_009E`, ACS table B05005: Period of entry by nativity and citizenship status in the United States
- Entered 1990 to 1999 foreign born — `B05005_014E`, ACS table B05005: Period of entry by nativity and citizenship status in the United States
- Entered before 1990 foreign born — `B05005_019E`, ACS table B05005: Period of entry by nativity and citizenship status in the United States

Left blank if any input is missing or the bottom number is zero.

### Foreign born entered 1990-1999

| | |
|---|---|
| Variable name | `FBENTERED1990S` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Of the foreign born, the share who entered the U.S. 1990-1999

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** Entered 1990 to 1999 foreign born — `B05005_014E`, ACS table B05005: Period of entry by nativity and citizenship status in the United States

**Bottom (denominator):** Foreign born by entry period, the sum of

- Entered 2010 or later foreign born — `B05005_004E`, ACS table B05005: Period of entry by nativity and citizenship status in the United States
- Entered 2000 to 2009 foreign born — `B05005_009E`, ACS table B05005: Period of entry by nativity and citizenship status in the United States
- Entered 1990 to 1999 foreign born — `B05005_014E`, ACS table B05005: Period of entry by nativity and citizenship status in the United States
- Entered before 1990 foreign born — `B05005_019E`, ACS table B05005: Period of entry by nativity and citizenship status in the United States

Left blank if any input is missing or the bottom number is zero.

### Foreign born entered before 1990

| | |
|---|---|
| Variable name | `FBENTEREDPRE1990` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Of the foreign born, the share who entered the U.S. before 1990

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** Entered before 1990 foreign born — `B05005_019E`, ACS table B05005: Period of entry by nativity and citizenship status in the United States

**Bottom (denominator):** Foreign born by entry period, the sum of

- Entered 2010 or later foreign born — `B05005_004E`, ACS table B05005: Period of entry by nativity and citizenship status in the United States
- Entered 2000 to 2009 foreign born — `B05005_009E`, ACS table B05005: Period of entry by nativity and citizenship status in the United States
- Entered 1990 to 1999 foreign born — `B05005_014E`, ACS table B05005: Period of entry by nativity and citizenship status in the United States
- Entered before 1990 foreign born — `B05005_019E`, ACS table B05005: Period of entry by nativity and citizenship status in the United States

Left blank if any input is missing or the bottom number is zero.

### Latin American foreign born entered 2010 or later

| | |
|---|---|
| Variable name | `LATAMFBENTERED2010PLUS` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Of the Latin-American foreign born, the share who entered the U.S. in 2010 or later

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** the sum of

- Latin America Caribbean entered 2010 or later — `B05007_042E`, ACS table B05007: Place of birth by year of entry by citizenship status for the foreign-born population
- Latin America Central America Mexico entered 2010 or later — `B05007_056E`, ACS table B05007: Place of birth by year of entry by citizenship status for the foreign-born population
- Latin America other Central America entered 2010 or later — `B05007_069E`, ACS table B05007: Place of birth by year of entry by citizenship status for the foreign-born population
- Latin America South America entered 2010 or later — `B05007_082E`, ACS table B05007: Place of birth by year of entry by citizenship status for the foreign-born population

**Bottom (denominator):** Latin America — `B05007_040E`, ACS table B05007: Place of birth by year of entry by citizenship status for the foreign-born population

Left blank if any input is missing or the bottom number is zero.

### Latin American foreign born entered 2000-2009

| | |
|---|---|
| Variable name | `LATAMFBENTERED2000S` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Of the Latin-American foreign born, the share who entered the U.S. 2000-2009

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** the sum of

- Latin America Caribbean entered 2000 to 2009 — `B05007_045E`, ACS table B05007: Place of birth by year of entry by citizenship status for the foreign-born population
- Latin America Central America Mexico entered 2000 to 2009 — `B05007_059E`, ACS table B05007: Place of birth by year of entry by citizenship status for the foreign-born population
- Latin America other Central America entered 2000 to 2009 — `B05007_072E`, ACS table B05007: Place of birth by year of entry by citizenship status for the foreign-born population
- Latin America South America entered 2000 to 2009 — `B05007_085E`, ACS table B05007: Place of birth by year of entry by citizenship status for the foreign-born population

**Bottom (denominator):** Latin America — `B05007_040E`, ACS table B05007: Place of birth by year of entry by citizenship status for the foreign-born population

Left blank if any input is missing or the bottom number is zero.

### Latin American foreign born entered 1990-1999

| | |
|---|---|
| Variable name | `LATAMFBENTERED1990S` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Of the Latin-American foreign born, the share who entered the U.S. 1990-1999

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** the sum of

- Latin America Caribbean entered 1990 to 1999 — `B05007_048E`, ACS table B05007: Place of birth by year of entry by citizenship status for the foreign-born population
- Latin America Central America Mexico entered 1990 to 1999 — `B05007_062E`, ACS table B05007: Place of birth by year of entry by citizenship status for the foreign-born population
- Latin America other Central America entered 1990 to 1999 — `B05007_075E`, ACS table B05007: Place of birth by year of entry by citizenship status for the foreign-born population
- Latin America South America entered 1990 to 1999 — `B05007_088E`, ACS table B05007: Place of birth by year of entry by citizenship status for the foreign-born population

**Bottom (denominator):** Latin America — `B05007_040E`, ACS table B05007: Place of birth by year of entry by citizenship status for the foreign-born population

Left blank if any input is missing or the bottom number is zero.

### Latin American foreign born entered before 1990

| | |
|---|---|
| Variable name | `LATAMFBENTEREDPRE1990` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Of the Latin-American foreign born, the share who entered the U.S. before 1990

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** the sum of

- Latin America Caribbean entered before 1990 — `B05007_051E`, ACS table B05007: Place of birth by year of entry by citizenship status for the foreign-born population
- Latin America Central America Mexico entered before 1990 — `B05007_065E`, ACS table B05007: Place of birth by year of entry by citizenship status for the foreign-born population
- Latin America other Central America entered before 1990 — `B05007_078E`, ACS table B05007: Place of birth by year of entry by citizenship status for the foreign-born population
- Latin America South America entered before 1990 — `B05007_091E`, ACS table B05007: Place of birth by year of entry by citizenship status for the foreign-born population

**Bottom (denominator):** Latin America — `B05007_040E`, ACS table B05007: Place of birth by year of entry by citizenship status for the foreign-born population

Left blank if any input is missing or the bottom number is zero.

### Hispanic moved within county

| | |
|---|---|
| Variable name | `HISPMOVEDWITHINCOUNTY` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Moved within the same county in the past year

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** Moved within same county — `B07004I_003E`, ACS table B07004I: Geographical mobility in the past year (Hispanic or Latino) for current residence in the United States

**Bottom (denominator):** Total — `B07004I_001E`, ACS table B07004I: Geographical mobility in the past year (Hispanic or Latino) for current residence in the United States

Left blank if any input is missing or the bottom number is zero.

### Hispanic moved from another county

| | |
|---|---|
| Variable name | `HISPMOVEDDIFFCOUNTY` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Moved from a different county in the same state

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** Moved from different county within same state — `B07004I_004E`, ACS table B07004I: Geographical mobility in the past year (Hispanic or Latino) for current residence in the United States

**Bottom (denominator):** Total — `B07004I_001E`, ACS table B07004I: Geographical mobility in the past year (Hispanic or Latino) for current residence in the United States

Left blank if any input is missing or the bottom number is zero.

### Hispanic moved from another state

| | |
|---|---|
| Variable name | `HISPMOVEDDIFFSTATE` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Moved from a different state

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** Moved from different state — `B07004I_005E`, ACS table B07004I: Geographical mobility in the past year (Hispanic or Latino) for current residence in the United States

**Bottom (denominator):** Total — `B07004I_001E`, ACS table B07004I: Geographical mobility in the past year (Hispanic or Latino) for current residence in the United States

Left blank if any input is missing or the bottom number is zero.

### Hispanic moved from abroad

| | |
|---|---|
| Variable name | `HISPMOVEDABROAD` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Moved from abroad in the past year

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** Moved from abroad — `B07004I_006E`, ACS table B07004I: Geographical mobility in the past year (Hispanic or Latino) for current residence in the United States

**Bottom (denominator):** Total — `B07004I_001E`, ACS table B07004I: Geographical mobility in the past year (Hispanic or Latino) for current residence in the United States

Left blank if any input is missing or the bottom number is zero.

### Hispanic population growth

| | |
|---|---|
| Variable name | `HISPGROWTH` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties only; left out of the tract dataset (the ingestion documentation explains why) |

**What it measures.** Change in the Hispanic population (B03001_003E) from the 2011-2015 ACS to the 2016-2020 ACS, as a log ratio: log(2020 + 1) - log(2015 + 1). Positive means growth.

**How it is calculated.**

Growth from the earlier period to the later one, measured as log(later + 1) - log(earlier + 1). Zero means no change, a positive value means growth, and a value of 0.1 is roughly 10% growth. The +1 keeps the measure defined where the earlier value is zero.

**Later:** Hispanic or Latino — `B03001_003E`, ACS table B03001: Hispanic or Latino origin by specific origin

**Earlier:** Hispanic or Latino, 2011-2015 ACS — `B03001_003E`, ACS table B03001: Hispanic or Latino origin by specific origin

Left blank if either period is missing.

### Foreign-born population growth

| | |
|---|---|
| Variable name | `FBGROWTH` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties only; left out of the tract dataset (the ingestion documentation explains why) |

**What it measures.** Change in the foreign-born population (B05002_013E) from the 2011-2015 ACS to the 2016-2020 ACS, as a log ratio. Positive means growth.

**How it is calculated.**

Growth from the earlier period to the later one, measured as log(later + 1) - log(earlier + 1). Zero means no change, a positive value means growth, and a value of 0.1 is roughly 10% growth. The +1 keeps the measure defined where the earlier value is zero.

**Later:** Foreign born — `B05002_013E`, ACS table B05002: Place of birth by nativity and citizenship status

**Earlier:** Foreign born, 2011-2015 ACS — `B05002_013E`, ACS table B05002: Place of birth by nativity and citizenship status

Left blank if either period is missing.
