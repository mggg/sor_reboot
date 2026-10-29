# National Origin and Background

Model group `national_origin`: 17 predictor(s). Regression runs select this group with `--groups national_origin`. See [how to read these pages](README.md).

| Variable | Name | Source | Role |
|---|---|---|---|
| Mexican origin | `MEXICANORIGIN` | ACS | predictor |
| Puerto Rican origin | `PUERTORICANORIGIN` | ACS | predictor |
| Cuban origin | `CUBANORIGIN` | ACS | predictor |
| Dominican origin | `DOMINICANORIGIN` | ACS | predictor |
| Central American origin | `CENTRALAMORIGIN` | ACS | predictor |
| Guatemalan origin | `GUATEMALANORIGIN` | ACS | predictor |
| Honduran origin | `HONDURANORIGIN` | ACS | predictor |
| Salvadoran origin | `SALVADORANORIGIN` | ACS | predictor |
| South American origin | `SOUTHAMORIGIN` | ACS | predictor |
| Colombian origin | `COLOMBIANORIGIN` | ACS | predictor |
| Ecuadorian origin | `ECUADORIANORIGIN` | ACS | predictor |
| Peruvian origin | `PERUVIANORIGIN` | ACS | predictor |
| Venezuelan origin | `VENEZUELANORIGIN` | ACS | predictor |
| Other Hispanic origin | `OTHERORIGINTOTAL` | ACS | predictor |
| Spaniard origin | `SPANIARDORIGIN` | ACS | predictor |
| Hispanic origin unspecified | `HISPORIGINUNSPECIFIED` | ACS | predictor |
| Foreign born from Latin America | `FBLATAMSHARE` | ACS | predictor |

## Variables

### Mexican origin

| | |
|---|---|
| Variable name | `MEXICANORIGIN` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Mexican origin. Top-level category; 58% of US Hispanics.

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** Hispanic or Latino Mexican — `B03001_004E`, ACS table B03001: Hispanic or Latino origin by specific origin

**Bottom (denominator):** Hispanic or Latino — `B03001_003E`, ACS table B03001: Hispanic or Latino origin by specific origin

Left blank if any input is missing or the bottom number is zero.

### Puerto Rican origin

| | |
|---|---|
| Variable name | `PUERTORICANORIGIN` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Puerto Rican origin. Top-level category.

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** Hispanic or Latino Puerto Rican — `B03001_005E`, ACS table B03001: Hispanic or Latino origin by specific origin

**Bottom (denominator):** Hispanic or Latino — `B03001_003E`, ACS table B03001: Hispanic or Latino origin by specific origin

Left blank if any input is missing or the bottom number is zero.

### Cuban origin

| | |
|---|---|
| Variable name | `CUBANORIGIN` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Cuban origin. Top-level category.

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** Hispanic or Latino Cuban — `B03001_006E`, ACS table B03001: Hispanic or Latino origin by specific origin

**Bottom (denominator):** Hispanic or Latino — `B03001_003E`, ACS table B03001: Hispanic or Latino origin by specific origin

Left blank if any input is missing or the bottom number is zero.

### Dominican origin

| | |
|---|---|
| Variable name | `DOMINICANORIGIN` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Dominican (Dominican Republic) origin. Top-level category.

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** Hispanic or Latino Dominican Dominican Republic — `B03001_007E`, ACS table B03001: Hispanic or Latino origin by specific origin

**Bottom (denominator):** Hispanic or Latino — `B03001_003E`, ACS table B03001: Hispanic or Latino origin by specific origin

Left blank if any input is missing or the bottom number is zero.

### Central American origin

| | |
|---|---|
| Variable name | `CENTRALAMORIGIN` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Central American origin, TOTAL across all countries. Contains the Guatemalan, Honduran and Salvadoran features below, plus Costa Rican, Nicaraguan and Panamanian, which are not modeled.

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** Hispanic or Latino central American — `B03001_008E`, ACS table B03001: Hispanic or Latino origin by specific origin

**Bottom (denominator):** Hispanic or Latino — `B03001_003E`, ACS table B03001: Hispanic or Latino origin by specific origin

Left blank if any input is missing or the bottom number is zero.

### Guatemalan origin

| | |
|---|---|
| Variable name | `GUATEMALANORIGIN` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Guatemalan origin. A subset of CENTRALAMORIGIN, not additional to it.

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** Hispanic or Latino central American Guatemalan — `B03001_010E`, ACS table B03001: Hispanic or Latino origin by specific origin

**Bottom (denominator):** Hispanic or Latino — `B03001_003E`, ACS table B03001: Hispanic or Latino origin by specific origin

Left blank if any input is missing or the bottom number is zero.

### Honduran origin

| | |
|---|---|
| Variable name | `HONDURANORIGIN` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Honduran origin. A subset of CENTRALAMORIGIN, not additional to it.

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** Hispanic or Latino central American Honduran — `B03001_011E`, ACS table B03001: Hispanic or Latino origin by specific origin

**Bottom (denominator):** Hispanic or Latino — `B03001_003E`, ACS table B03001: Hispanic or Latino origin by specific origin

Left blank if any input is missing or the bottom number is zero.

### Salvadoran origin

| | |
|---|---|
| Variable name | `SALVADORANORIGIN` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Salvadoran origin. A subset of CENTRALAMORIGIN, not additional to it.

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** Hispanic or Latino central American Salvadoran — `B03001_014E`, ACS table B03001: Hispanic or Latino origin by specific origin

**Bottom (denominator):** Hispanic or Latino — `B03001_003E`, ACS table B03001: Hispanic or Latino origin by specific origin

Left blank if any input is missing or the bottom number is zero.

### South American origin

| | |
|---|---|
| Variable name | `SOUTHAMORIGIN` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** South American origin, TOTAL across all countries. Contains the Colombian, Ecuadorian, Peruvian and Venezuelan features below, plus six smaller nationalities that are not modeled.

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** Hispanic or Latino south American — `B03001_016E`, ACS table B03001: Hispanic or Latino origin by specific origin

**Bottom (denominator):** Hispanic or Latino — `B03001_003E`, ACS table B03001: Hispanic or Latino origin by specific origin

Left blank if any input is missing or the bottom number is zero.

### Colombian origin

| | |
|---|---|
| Variable name | `COLOMBIANORIGIN` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Colombian origin. A subset of SOUTHAMORIGIN, not additional to it.

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** Hispanic or Latino south American Colombian — `B03001_020E`, ACS table B03001: Hispanic or Latino origin by specific origin

**Bottom (denominator):** Hispanic or Latino — `B03001_003E`, ACS table B03001: Hispanic or Latino origin by specific origin

Left blank if any input is missing or the bottom number is zero.

### Ecuadorian origin

| | |
|---|---|
| Variable name | `ECUADORIANORIGIN` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Ecuadorian origin. A subset of SOUTHAMORIGIN, not additional to it.

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** Hispanic or Latino south American Ecuadorian — `B03001_021E`, ACS table B03001: Hispanic or Latino origin by specific origin

**Bottom (denominator):** Hispanic or Latino — `B03001_003E`, ACS table B03001: Hispanic or Latino origin by specific origin

Left blank if any input is missing or the bottom number is zero.

### Peruvian origin

| | |
|---|---|
| Variable name | `PERUVIANORIGIN` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Peruvian origin. A subset of SOUTHAMORIGIN, not additional to it.

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** Hispanic or Latino south American Peruvian — `B03001_023E`, ACS table B03001: Hispanic or Latino origin by specific origin

**Bottom (denominator):** Hispanic or Latino — `B03001_003E`, ACS table B03001: Hispanic or Latino origin by specific origin

Left blank if any input is missing or the bottom number is zero.

### Venezuelan origin

| | |
|---|---|
| Variable name | `VENEZUELANORIGIN` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Venezuelan origin. A subset of SOUTHAMORIGIN, not additional to it.

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** Hispanic or Latino south American Venezuelan — `B03001_025E`, ACS table B03001: Hispanic or Latino origin by specific origin

**Bottom (denominator):** Hispanic or Latino — `B03001_003E`, ACS table B03001: Hispanic or Latino origin by specific origin

Left blank if any input is missing or the bottom number is zero.

### Other Hispanic origin

| | |
|---|---|
| Variable name | `OTHERORIGINTOTAL` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Other Hispanic or Latino, TOTAL: everyone whose reported origin is not Mexican, Puerto Rican, Cuban, Dominican, Central American or South American. 5.5% of US Hispanics. Contains the two features below.

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** Other Hispanic or Latino — `B03001_027E`, ACS table B03001: Hispanic or Latino origin by specific origin

**Bottom (denominator):** Hispanic or Latino — `B03001_003E`, ACS table B03001: Hispanic or Latino origin by specific origin

Left blank if any input is missing or the bottom number is zero.

### Spaniard origin

| | |
|---|---|
| Variable name | `SPANIARDORIGIN` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Spaniard (origin in Spain). A subset of OTHERORIGINTOTAL.

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** Other Hispanic or Latino Spaniard — `B03001_028E`, ACS table B03001: Hispanic or Latino origin by specific origin

**Bottom (denominator):** Hispanic or Latino — `B03001_003E`, ACS table B03001: Hispanic or Latino origin by specific origin

Left blank if any input is missing or the bottom number is zero.

### Hispanic origin unspecified

| | |
|---|---|
| Variable name | `HISPORIGINUNSPECIFIED` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Reported a Hispanic or Latino identity but no specific national origin: write-ins such as "Hispanic", "Latino" or "Latin American", plus origins too small for the Census to tabulate separately. A subset of OTHERORIGINTOTAL, and 57% of it. 1.95 million people, 3.1% of US Hispanics.

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** All other Hispanic or Latino — `B03001_031E`, ACS table B03001: Hispanic or Latino origin by specific origin

**Bottom (denominator):** Hispanic or Latino — `B03001_003E`, ACS table B03001: Hispanic or Latino origin by specific origin

Left blank if any input is missing or the bottom number is zero.

### Foreign born from Latin America

| | |
|---|---|
| Variable name | `FBLATAMSHARE` |
| Source | American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Of the foreign born, the share born in Latin America (naturalized plus non-citizen)

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** the sum of

- Foreign born naturalized U.S. citizen Latin America — `B05002_019E`, ACS table B05002: Place of birth by nativity and citizenship status
- Foreign born not a U.S. citizen Latin America — `B05002_026E`, ACS table B05002: Place of birth by nativity and citizenship status

**Bottom (denominator):** Foreign born — `B05002_013E`, ACS table B05002: Place of birth by nativity and citizenship status

Left blank if any input is missing or the bottom number is zero.
