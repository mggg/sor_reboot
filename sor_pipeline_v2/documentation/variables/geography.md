# Geography

Model group `geography`: 4 predictor(s). Regression runs select this group with `--groups geography`. See [how to read these pages](README.md).

| Variable | Name | Source | Role |
|---|---|---|---|
| Latitude | `INTPTLAT` | TIGER | predictor |
| Longitude | `INTPTLON` | TIGER | predictor |
| Population density | `DENSITY` | TIGER | predictor |
| Urban population share | `URBANSHARE` | DHC | predictor |

## Variables

### Latitude

| | |
|---|---|
| Variable name | `INTPTLAT` |
| Source | Census TIGER/Line 2020 shapefiles |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Latitude of the unit's internal point (TIGER/Line 2020)

**How it is calculated.**

Taken directly from Latitude, itself a computed variable — `INTPTLAT`, unchanged.

### Longitude

| | |
|---|---|
| Variable name | `INTPTLON` |
| Source | Census TIGER/Line 2020 shapefiles |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Longitude of the unit's internal point (TIGER/Line 2020)

**How it is calculated.**

Taken directly from Longitude, itself a computed variable — `INTPTLON`, unchanged.

### Population density

| | |
|---|---|
| Variable name | `DENSITY` |
| Source | Census TIGER/Line 2020 shapefiles |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Population density: PL total population divided by TIGER land area (ALAND); NaN where a unit has no land area

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** Total population, itself a computed variable — `TOTALPOP`

**Bottom (denominator):** Land area in square meters (TIGER/Line) — `ALAND`

Left blank if any input is missing or the bottom number is zero.

### Urban population share

| | |
|---|---|
| Variable name | `URBANSHARE` |
| Source | 2020 Decennial Census, Demographic and Housing Characteristics file |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Share of the unit's total population living in an urban area (2020 Census urban/rural classification)

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** Urban — `DHC_P2_002N`, DHC table P2: Urban and rural

**Bottom (denominator):** Total — `DHC_P2_001N`, DHC table P2: Urban and rural

Left blank if any input is missing or the bottom number is zero.
