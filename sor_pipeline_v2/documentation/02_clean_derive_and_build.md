# Cleaning, Deriving, and Building the Dataset

The ingest stage (see [01_raw_data_ingestion.md](01_raw_data_ingestion.md)) ends with one raw dataset per geographic level (county and tract), raw.parquet, holding every source column exactly as received from the original source build. This resulted in 254 input columns (counts and estimates that features are built from), 175 margin-of-error columns, and 2 identifiers for both the county and tract level raw.parquet files. This document covers how the raw files become the processed dataset for analysis. The derive stage turns the raw columns into the dataset's variables using arithmetic alone: nothing is fetched, estimated, or filled in. The result is cut down to a fixed set of columns and saved as processed.parquet—134 columns for counties and 131 for tracts—which is the dataset every model reads. Because the derive stage depends only on raw.parquet, it can be rerun at any time without touching the sources. Each variable's own definition is written out in plain English in the [variable pages](variables/README.md).

## Contents

- [The Derive Steps](#the-derive-steps)
- [Blank Values](#blank-values)
- [The Processed Dataset](#the-processed-dataset)
- [Running the Build](#running-the-build)
- [Source Checksums](#source-checksums)

## The Derive Steps

The derive stage runs six steps in a fixed order. The order matters because some variables are built from others: population density divides the total population, which the PL step creates, and voter turnout divides by the citizen voting-age population, which the ACS step creates. Steps 2 through 5 each check, before computing anything, that every column they need is present, and stop the build with an error naming the step that should have created a missing one. Step 1 reads only raw PL columns, and it checks on finishing that every column it is meant to create exists.

### Step 0: Converting Text to Numbers

The census sources deliver every value as text, which is what keeps leading zeros on GEOIDs, and raw.parquet stores them in this format. The first step converts every column except the identifier (GEOID) and the unit name (NAME) to numbers. Any value that cannot be read as a number becomes blank.

### Step 1: PL Counts, Targets, and Classification

The PL step builds the outcome side of the dataset, in four stages, each reading what the one before it created:

1. **Population counts.** Each count is taken directly from one line of the PL tables or summed across several; White alone or in combination, for example, sums the 32 lines of table P1 that include White.
2. **Hispanic-of-race counts.** The PL file publishes no direct count of, for example, Hispanic residents who chose Some Other Race alone, so each of these counts is computed as the count for everyone minus the count for non-Hispanic residents.
3. **Shares.** Each Hispanic-of-race count is divided by the Hispanic population or by the total population. The four shares of the Hispanic population are what the regression predicts.
4. **Dominant-race classification.** For each unit, which of three groups of Hispanic residents is largest: those who chose Some Other Race alone, White and Some Other Race, or White alone.

Every column this step creates is described on the [targets page](variables/targets.md).

### Step 2: ACS Variables

Where the ACS cannot publish an estimate, it substitutes a special negative code rather than leaving the value empty. These codes look like real numbers, so arithmetic run on them would produce results that look plausible but mean nothing. Before computing anything, this step therefore replaces all six codes with blank values, in every numeric column:

| Code | Meaning |
|---|---|
| -666666666 | Estimate cannot be computed (too few sample cases) |
| -999999999 | Estimate not available |
| -555555555 | Margin cannot be computed, or falls in the lowest or highest interval |
| -222222222 | Estimate controlled; margin not appropriate |
| -333333333 | Margin not appropriate for this median |
| -888888888 | Not applicable |

It then computes every declared ACS variable: shares and ratios of table lines, values taken directly from a table (such as a median), and the two growth variables, which compare each 2016–2020 estimate against its 2011–2015 counterpart. The margins of error fetched alongside every estimate are kept in raw.parquet (173 columns at the county level) but are not used by any step and do not appear in processed.parquet.

### Step 3: Urban Share (DHC)

The DHC step divides each unit's urban population by its total population, both from the DHC file. As full-count data, the DHC has no special codes or margins of error, so nothing needs replacing first.

### Step 4: Geometry

Latitude and longitude of each unit's internal point pass through unchanged. Population density divides the PL total population, created in Step 1, by the land area in square meters, so it is measured in people per square meter. Density is left blank where a unit has no land area: no county is affected, but 361 tracts are.

### Step 5: Election

The election step computes the two-party lean for 2020 and for 2016, the change in lean between them (computed from the two leans, so they come first), the number of two-party votes cast, voter turnout, and the growth in the Democratic and the Republican vote from 2016 to 2020. All are built from the four vote columns of the GerryDB release, plus, for turnout, the ACS denominator. Voter turnout is computed for counties only: its denominator, the citizen voting-age population, comes from the ACS, whose tract estimates are too uncertain to divide by. The ingestion document gives the numbers. DC and Puerto Rico, which have no votes in the release, come out blank in every election variable.

## Blank Values

The derive stage never removes a unit: every county or tract on the PL spine appears in processed.parquet, whatever its values. Instead, a variable is left blank wherever it cannot be computed honestly. There are four rules:

- **A missing input makes the result blank.** Sums, shares, and differences do not skip missing pieces, because a total built from only some of its parts would look complete and be wrong.
- **A zero denominator makes a share blank**, since a share of nothing is undefined. A two-party lean is likewise blank where both parties have zero votes, which only occurs in about 600 tracts.
- **A growth variable is blank** where either period is missing.
- **Nothing is filled in.** No blank is replaced by an estimate, an average, or a zero.

In practice, blanks come from three places: a source that has no data for a unit (DC and Puerto Rico's votes, or the 10,682 tracts for which the ACS publishes no Hispanic per capita income), the ACS's special codes, and zero denominators. Dropping incomplete units is left to the models: the regression fits only on units with every variable present.

## The Processed Dataset

processed.parquet keeps a fixed list of columns, in this order:

| Columns | Count |
|---|---|
| GEOID | 1 |
| PL population counts | 10 |
| Hispanic-of-race counts | 8 |
| Targets: the nine outcome shares and four classification columns | 13 |
| Predictors, in model group order | 101 (98 for tracts) |
| Context: the citizen voting-age population, kept for reference | 1 |
| **Total** | **134 (131 for tracts)** |

Everything else stays in raw.parquet only: the raw census codes, the margins of error, the 2011–2015 columns, the raw vote columns, and the unit name. The tract dataset leaves out three predictors: Hispanic population growth and foreign-born population growth, which are computed at the tract level but not saved, and voter turnout, which is not computed at all. The ingestion document explains both decisions. The column list is defined in build_dataset/processed_schema.py, and the model groups it draws on in build_dataset/model_groups.py.

Before saving, the build confirms that every column on the list was actually derived. If one is missing, it stops with an error and processed.parquet is not written, so a dataset whose columns disagree with the declared variables can never be saved.

## Running the Build

The build needs a Census API key, set as CENSUS_API_KEY in the .env file that utils/config.py points to, and the GerryDB release in data/RELEASE_geopackages. Every command runs from sor_pipeline_v2:

| To build | Command |
|---|---|
| All counties | `uv run python -m build_dataset.main_build` |
| All tracts | `uv run python -m build_dataset.main_build --level national_tracts` |
| Tracts in some states | `uv run python -m build_dataset.main_build --level national_tracts --states 06 44` |

Each build writes two files:

| Build | Raw dataset | Processed dataset |
|---|---|---|
| All counties | data/national/counties/raw.parquet | data/national/counties/processed.parquet |
| All tracts | data/national/tracts/raw.parquet | data/national/tracts/processed.parquet |
| Tracts in some states | data/national/tracts/raw_states-06-44.parquet | data/national/tracts/processed_states-06-44.parquet |

A partial tract build names its files after its states, so it can never overwrite the national tract dataset. The --states option is ignored for the county build, which is always national.

**Re-deriving without fetching.** Adding --from-raw to any command skips the ingest stage: the build reads the raw.parquet already on disk, reruns the derive steps, and rewrites only processed.parquet. This is the right choice for any change downstream of ingestion, such as a renamed variable, a new derived variable, or a changed formula. It cannot detect a change in the sources themselves, and it stops with an error if the raw dataset does not exist yet.

**What the build prints.** The county build prints one line per source, saying how many counties on the spine that source left without data, so a gap in coverage shows up as soon as it appears. The tract build shows a progress bar by state and prints the same totals once at the end.

**Caching.** The first build downloads every census source and stores it under data/national/raw. Later builds read those files instead of the API, so they run offline, and an interrupted tract build picks up from the states already stored.

## Source Checksums

The file source_records/raw_checksums.json records a SHA-256 checksum—a fingerprint that changes if a single byte of a file changes—for every source file the builds read: the six county inputs (five census files and the county geometry), the six files each state contributes to the tract build (five census files and the tract geometry), and the GerryDB county and tract views. With every state built, that is 418 files. Each is recorded under its path relative to the data directory, for example national/raw/dhc_national_counties.csv.

| To | Command |
|---|---|
| Check every file against the record | `uv run python -m build_dataset.ingest.fetch_and_store.checksums` |
| Record the files as they stand now | `uv run python -m build_dataset.ingest.fetch_and_store.checksums --write` |
| Remove records for sources no longer used | `uv run python -m build_dataset.ingest.fetch_and_store.checksums --forget KEY ...` |

Checking lists every file that is not a match, then a count of each outcome: **match** (unchanged), **MISMATCH** (the file has changed since it was recorded), **absent** (recorded, but no longer on disk), or **unrecorded** (on disk, but never recorded). A mismatch in a census file is expected after a newly declared variable makes the build refetch it; a mismatch in a GerryDB view means the release file itself was replaced. Either way, confirm that is what happened, then record the new state with --write.

Recording never deletes anything: a record for a file that has since been removed from disk is kept, so the record still says what the dataset was built from. --forget is the only way to remove one. Recording also refuses to run if any of the six county inputs is missing, so run the county build first.
