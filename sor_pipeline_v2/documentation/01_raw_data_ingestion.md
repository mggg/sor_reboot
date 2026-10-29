# Data Ingestion

There are five primary data sources from which the dataset is built: (1) the 2020 Decennial Census P.L. 94-171 Redistricting file (PL), (2) the 2020 Decennial Census Demographic and Housing Characteristics file (DHC), (3) the American Community Survey five-year estimates (ACS), (4) TIGER/Line geometry files from the U.S. Census Bureau, and (5) presidential election returns from the MGGG Lab's GerryDB release. Each source is fetched or loaded by its own ingest module, reduced to the columns the pipeline's declared features read, and merged on GEOID into one raw dataset per level (counties/raw.parquet or tracts/raw.parquet), which preserves every value as the source delivered it and serves as the audit trail for everything downstream. Downloaded sources are cached after the initial run: each is fetched only if its file is not already in the raw data directory, and a cached census file that lacks a column required by a newly declared feature is refetched and overwritten. This means that repeated builds run offline and reproduce byte-identical inputs.

The dataset is built at two geographic levels—counties and tracts—from the same sources, and for the most part, the two levels include the same declared features. The three features missing at the tract level are Hispanic population growth (ACS), foreign-born population growth (ACS), and voter turnout (election); each is discussed under its source below. The county build covers 3,221 counties (the 50 states, DC, and Puerto Rico) and fetches each census source nationally, in one pull per source. The tract build covers 85,395 tracts across the same 52 jurisdictions, but fetches them one state at a time, because the Census API refuses a state wildcard below the county level. Each state's pull is cached as its own file, so an interrupted tract build resumes from the states already on disk, and a build of only some states writes its raw and processed files under state-labeled filenames so that they cannot overwrite the national ones. Both levels read their election returns from the same release, described below.

## Contents

*   [Decennial Census PL Data](#decennial-census-pl-data)
*   [Demographic and Housing Characteristics (DHC) Data](#demographic-and-housing-characteristics-dhc-data)
*   [American Community Survey (ACS) Data](#american-community-survey-acs-data)
*   [Geometry Data](#geometry-data)
*   [Election Data](#election-data)

## Decennial Census PL Data

### Sourcing

The Decennial Census P.L. 94-171 Redistricting (PL) data was sourced from the [Census API](https://www.census.gov/data/developers/data-sets/decennial-census.html). Two tables are fetched: P1, race counts for the total population, and P2, the same race counts split by Hispanic or Latino origin. As full-count enumeration data, the PL values are counts with no margins of error—the decennial counterpart of the ACS's estimate-and-MOE pairs. The request lists are derived from the declared features (35 variable codes per table). At the county level each table is fetched for every county in one national request; at the tract level it is fetched for every tract one state at a time. Each pull is cached on disk as a CSV.

### Cleaning

Cleaning at ingest is minimal: a GEOID is assembled from each row's state and county codes (five digits) or state, county, and tract codes (eleven digits), values are kept as the API delivers them, and because the P1 and P2 tables share no variable-code names with each other, no renaming is required. The PL total-population frame additionally serves as the spine of the merged dataset: every other source is left-joined onto its GEOIDs (3,221 counties, or 85,395 tracts), so a unit another source is silent about appears with missing values rather than disappearing from the dataset.

## Demographic and Housing Characteristics (DHC) Data

### Sourcing

The Demographic and Housing Characteristics (DHC) data was sourced from the [Census API](https://www.census.gov/data/developers/data-sets/decennial-census.html), for every county in one national request at the county level and for every tract one state at a time at the tract level.

### Cleaning

Because the Census API allows the exact variables to be specified per request, only the desired columns—the urban population and total population—are fetched, and in turn, almost no cleaning is required. The one transformation is a rename: DHC's table P2 shares variable-code names with the PL file's table P2 (P2\_001N is the total population here and the Hispanic-or-Latino universe there), so the DHC columns are prefixed with "DHC\_" to prevent the two surveys from colliding in the merged dataset.

## American Community Survey (ACS) Data

### Sourcing

The American Community Survey (ACS) data was sourced from the [Census API](https://www.census.gov/data/developers/data-sets/acs-5year.html) in two five-year vintages: the 2016–2020 estimates, which supply most ACS features, and the 2011–2015 estimates, which supply the prior-year inputs of the two growth features. The request lists are derived from the declared features themselves: every estimate column a feature reads is fetched together with its margin-of-error twin, giving 346 columns for 2016–2020 and 4 for 2011–2015. Because the Census API limits each request to 50 variables, the fetch is issued in batches that are joined back together on GEOID. Both vintages are fetched nationally for counties and one state at a time for tracts, and each assembled pull is cached on disk as a CSV.

### Cleaning

Because the API returns exactly the requested columns, cleaning at ingest is minimal. A GEOID is assembled from each row's state and county codes (and tract code, at the tract level), and values are kept as the API delivers them, including the Census's suppression sentinels, which are handled later in the derive stage. The one real transformation concerns the 2011–2015 vintage: every ACS vintage publishes identical variable codes, so the prior columns are renamed with a "\_PRIOR" suffix (e.g., B03001\_003E becomes B03001\_003E\_PRIOR) to prevent them from colliding with their 2016–2020 counterparts when the two vintages are merged into one dataset.

Because the two vintages are joined by GEOID, a unit whose boundaries changed between them has no prior values. At the county level this affects only Chugach and Copper River, AK, which were created in 2019. At the tract level it is far more common: the 2011–2015 estimates are published on 2010 tract boundaries, so the 22,873 tracts that were redrawn for 2020 (27% of the 85,395) have no 2015 counterpart and carry missing prior values.

This gap is why Hispanic population growth and foreign-born population growth, the two features built from the 2011–2015 vintage, are left out of the tract dataset. Their prior-vintage inputs are still fetched and kept in tracts/raw.parquet, but the regression fits only on units with every feature present, so including either feature would remove those 22,873 tracts from every model. The county dataset keeps both, since only two counties lack them there.

## Geometry Data

### Sourcing

The geometry data was sourced from the [TIGER/Line shapefiles](https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html) stored on the Census website: the 2020 national county file for the county build, and the 2020 per-state tract files, downloaded one state at a time, for the tract build.

### Cleaning

Because the GEOIDs are already zero-padded (five digits for counties, eleven for tracts), minimal cleaning is required with downloaded TIGER/Line shapefiles. The entire file is saved on disk, but when assembling the raw.parquet for the regression pipeline, only the GEOID, unit name, land area (in square meters), internal point latitude, and internal point longitude are returned.

## Election Data

### Sourcing

The election data was sourced from MGGG's GerryDB release (the Districtr v2 views), delivered as one geopackage per state per geography level for the 50 states; the county build reads the county views and the tract build reads the tract views. The release's 2016 and 2020 presidential vote counts were obtained from [Dave's Redistricting block data](https://github.com/dra2020/block_data) in January 2025 and carried onto 2020 census counties and tracts, so the release's identifiers are official 2020 GEOIDs that join the PL spine directly. Because both levels come from the same block data, a state's tract votes sum exactly to its county votes. The release is read as published on every build; nothing is fetched or cached.

### Cleaning

The release requires almost no cleaning. Only the unit identifier (stored in a column named "path") and the four presidential vote columns—Democratic and Republican votes for 2020 and 2016—are read, and the geometry is ignored, since TIGER/Line already supplies it. The vote columns are renamed to the pipeline's own names, and before the merge the pipeline checks that every identifier is a GEOID of the level's width (five digits for counties, eleven for tracts), that none repeats, and that all belong to the state being read. The release has no views for DC or Puerto Rico, so neither has votes at either level: 79 counties (DC and Puerto Rico's 78 municipios) and 1,187 tracts (206 in DC, 981 in Puerto Rico). Puerto Rico casts no presidential ballots.

Voter turnout—the two-party 2020 presidential vote divided by the citizen voting-age population—is left out of the tract dataset. The problem is the denominator, not the votes: the citizen voting-age population comes from the ACS five-year estimates, whose error on a single tract is large enough that 2,414 of the 83,389 tracts with a defined turnout report more votes cast than voting-age citizens, the worst by a factor of 16.5. At the county level the same calculation exceeds 1.0 in only 6 of 3,142 counties, so the county dataset keeps turnout.