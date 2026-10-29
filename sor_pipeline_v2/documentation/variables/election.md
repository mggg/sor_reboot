# Elections

Model group `election`: 7 predictor(s). Regression runs select this group with `--groups election`. See [how to read these pages](README.md).

| Variable | Name | Source | Role |
|---|---|---|---|
| Two-party vote lean, 2020 | `VOTELEAN20` | ELECTION | predictor |
| Two-party vote lean, 2016 | `VOTELEAN16` | ELECTION | predictor |
| Change in two-party lean, 2016 to 2020 | `VOTELEANCHANGE` | ELECTION | predictor |
| Two-party votes cast | `NUMBEROFVOTERS` | ELECTION | predictor |
| Voter turnout | `TURNOUT` | ELECTION | predictor |
| Democratic vote growth | `DEMGROWTH` | ELECTION | predictor |
| Republican vote growth | `REPGROWTH` | ELECTION | predictor |

## Variables

### Two-party vote lean, 2020

| | |
|---|---|
| Variable name | `VOTELEAN20` |
| Source | MGGG GerryDB release (presidential returns from Dave's Redistricting block data) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** (Republican - Democratic) share of the two-party 2020 presidential vote; positive = Republican-leaning

**How it is calculated.**

A balance between two sides, on a scale from -1 to +1: (first side - second side) / (first side + second side). +1 means entirely the first side, -1 entirely the second, 0 an even split.

**First side:** Republican presidential votes, 2020 (GerryDB release column `pres_20_rep`) — `E_20_PRES_REP`

**Second side:** Democratic presidential votes, 2020 (GerryDB release column `pres_20_dem`) — `E_20_PRES_DEM`

Left blank if any input is missing or both sides are zero.

### Two-party vote lean, 2016

| | |
|---|---|
| Variable name | `VOTELEAN16` |
| Source | MGGG GerryDB release (presidential returns from Dave's Redistricting block data) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** (Republican - Democratic) share of the two-party 2016 presidential vote; positive = Republican-leaning

**How it is calculated.**

A balance between two sides, on a scale from -1 to +1: (first side - second side) / (first side + second side). +1 means entirely the first side, -1 entirely the second, 0 an even split.

**First side:** Republican presidential votes, 2016 (GerryDB release column `pres_16_rep`) — `E_16_PRES_REP`

**Second side:** Democratic presidential votes, 2016 (GerryDB release column `pres_16_dem`) — `E_16_PRES_DEM`

Left blank if any input is missing or both sides are zero.

### Change in two-party lean, 2016 to 2020

| | |
|---|---|
| Variable name | `VOTELEANCHANGE` |
| Source | MGGG GerryDB release (presidential returns from Dave's Redistricting block data) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** 2020 lean minus 2016 lean, in margin points: positive = moved Republican. A tract can be strongly Democratic and still have a large positive value -- this measures the direction it moved, not where it stands. Margin moves twice as far as vote share, since a switched vote is added to one side and taken off the other.

**How it is calculated.**

One value minus another.

**Start from:** Two-party vote lean, 2020, itself a computed variable — `VOTELEAN20`

**Subtract:** Two-party vote lean, 2016, itself a computed variable — `VOTELEAN16`

Left blank if either input is missing.

### Two-party votes cast

| | |
|---|---|
| Variable name | `NUMBEROFVOTERS` |
| Source | MGGG GerryDB release (presidential returns from Dave's Redistricting block data) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Total two-party 2020 presidential vote (Dem + Rep)

**How it is calculated.**

The sum of:

- Democratic presidential votes, 2020 (GerryDB release column `pres_20_dem`) — `E_20_PRES_DEM`
- Republican presidential votes, 2020 (GerryDB release column `pres_20_rep`) — `E_20_PRES_REP`

Left blank if any input is missing.

### Voter turnout

| | |
|---|---|
| Variable name | `TURNOUT` |
| Source | MGGG GerryDB release (presidential returns from Dave's Redistricting block data) |
| Role | Predictor: an input the models use |
| Available for | Counties only; left out of the tract dataset (the ingestion documentation explains why) |

**What it measures.** Two-party 2020 presidential votes cast per voting-age citizen

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** the sum of

- Democratic presidential votes, 2020 (GerryDB release column `pres_20_dem`) — `E_20_PRES_DEM`
- Republican presidential votes, 2020 (GerryDB release column `pres_20_rep`) — `E_20_PRES_REP`

**Bottom (denominator):** Citizen voting-age population, itself a computed variable — `VOTINGAGEPOP`

Left blank if any input is missing or the bottom number is zero.

### Democratic vote growth

| | |
|---|---|
| Variable name | `DEMGROWTH` |
| Source | MGGG GerryDB release (presidential returns from Dave's Redistricting block data) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Log growth of the Democratic presidential vote from 2016 to 2020: log1p(2020 votes) - log1p(2016 votes)

**How it is calculated.**

Growth from the earlier period to the later one, measured as log(later + 1) - log(earlier + 1). Zero means no change, a positive value means growth, and a value of 0.1 is roughly 10% growth. The +1 keeps the measure defined where the earlier value is zero.

**Later:** Democratic presidential votes, 2020 (GerryDB release column `pres_20_dem`) — `E_20_PRES_DEM`

**Earlier:** Democratic presidential votes, 2016 (GerryDB release column `pres_16_dem`) — `E_16_PRES_DEM`

Left blank if either period is missing.

### Republican vote growth

| | |
|---|---|
| Variable name | `REPGROWTH` |
| Source | MGGG GerryDB release (presidential returns from Dave's Redistricting block data) |
| Role | Predictor: an input the models use |
| Available for | Counties and tracts |

**What it measures.** Log growth of the Republican presidential vote from 2016 to 2020: log1p(2020 votes) - log1p(2016 votes)

**How it is calculated.**

Growth from the earlier period to the later one, measured as log(later + 1) - log(earlier + 1). Zero means no change, a positive value means growth, and a value of 0.1 is roughly 10% growth. The +1 keeps the measure defined where the earlier value is zero.

**Later:** Republican presidential votes, 2020 (GerryDB release column `pres_20_rep`) — `E_20_PRES_REP`

**Earlier:** Republican presidential votes, 2016 (GerryDB release column `pres_16_rep`) — `E_16_PRES_REP`

Left blank if either period is missing.
