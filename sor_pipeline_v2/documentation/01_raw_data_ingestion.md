# Data Ingestion

There are five primary data sources from which the county-level dataset is built: the 2020 Decennial Census P.L. 94-171 Redistricting file (PL), the 2020 Decennial Census Demographic and Housing Characteristics file (DHC), the American Community Survey five-year estimates (ACS), TIGER/Line county geometry, and county-level presidential election returns. Each source is fetched or loaded by its own ingest module, reduced to the columns the pipeline's declared features read, and merged on county GEOID into a single raw dataset (raw.parquet), which preserves every value as the source delivered it and serves as the audit trail for everything downstream. Downloaded sources are cached: each is fetched only if its file is not already in the raw data directory, and a cached file that lacks a column required by a newly declared feature is refetched and overwritten, so repeated builds run offline and reproduce byte-identical inputs.

## Contents

- [Decennial Census PL Data](#decennial-census-pl-data)
- [Demographic and Housing Characteristics (DHC) Data](#demographic-and-housing-characteristics-dhc-data)
- [American Community Survey (ACS) Data](#american-community-survey-acs-data)
- [Geometry Data](#geometry-data)
- [Election Data](#election-data)

## Decennial Census PL Data

### Sourcing

The Decennial Census P.L. 94-171 Redistricting (PL) data was sourced from the [Census API](https://www.census.gov/data/developers/data-sets/decennial-census.html). Two tables are fetched for every county at the national level: P1, race counts for the total population, and P2, the same race counts split by Hispanic or Latino origin. As full-count enumeration data, the PL values are counts with no margins of error—the decennial counterpart of the ACS's estimate-and-MOE pairs. The request lists are derived from the declared features (35 variable codes per table), and the national all-counties pull of each table is cached on disk as a CSV.

### Cleaning

Cleaning at ingest is minimal: a five-digit GEOID is assembled from each row's state and county codes, values are kept as the API delivers them, and because the P1 and P2 tables share no variable-code names with each other, no renaming is required. The PL total-population frame additionally serves as the spine of the merged dataset: every other source is left-joined onto its 3,221 county GEOIDs, so a county another source is silent about appears with missing values rather than disappearing from the dataset.

## Demographic and Housing Characteristics (DHC) Data

### Sourcing

The Demographic and Housing Characteristics (DHC) data was sourced from the [Census API](https://www.census.gov/data/developers/data-sets/decennial-census.html).

### Cleaning

Because the Census API allows the exact variables to be specified per request, only the desired columns—the urban population and total population—are fetched for every county at the national level, and in turn, almost no cleaning is required. The one transformation is a rename: DHC's table P2 shares variable-code names with the PL file's table P2 (P2_001N is the total population here and the Hispanic-or-Latino universe there), so the DHC columns are prefixed with "DHC_" to prevent the two surveys from colliding in the merged dataset.

## American Community Survey (ACS) Data

### Sourcing

The American Community Survey (ACS) data was sourced from the [Census API](https://www.census.gov/data/developers/data-sets/acs-5year.html) in two five-year vintages: the 2016–2020 estimates, which supply most ACS features, and the 2011–2015 estimates, which supply the prior-year inputs of the two growth features. The request lists are derived from the declared features themselves: every estimate column a feature reads is fetched together with its margin-of-error twin, giving 346 columns for 2016–2020 and 4 for 2011–2015. Because the Census API limits each request to 50 variables, the fetch is issued in batches that are joined back together on GEOID, and the assembled national all-counties pull of each vintage is cached on disk as a CSV.

### Cleaning

Because the API returns exactly the requested columns, cleaning at ingest is minimal. A five-digit GEOID is assembled from each row's state and county codes, and values are kept as the API delivers them, including the Census's suppression sentinels, which are handled later in the derive stage. The one real transformation concerns the 2011–2015 vintage: every ACS vintage publishes identical variable codes, so the prior columns are renamed with a "_PRIOR" suffix (e.g., B03001_003E becomes B03001_003E_PRIOR) to prevent them from colliding with their 2016–2020 counterparts when the two vintages are merged into one dataset.

## Geometry Data

### Sourcing

The geometry data for all counties was sourced from the [TIGER/Line shapefiles](https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html) stored on the Census website.

### Cleaning

Because the GEOIDs are already zero-padded to be five digits long, minimal cleaning is required with downloaded TIGER/Line shapefiles. The entire file is saved on disk, but when assembling the raw.parquet for the regression pipeline, only the GEOID, county name, land area (in square meters), internal point latitude, and internal point longitude are returned.

## Election Data

### Sourcing

The election data was sourced from the MIT Election Data and Science Lab at the Harvard Dataverse website ([doi:10.7910/DVN/VOQCHQ](https://doi.org/10.7910/DVN/VOQCHQ)), with Universal Numerical Fingerprint (UNF): "6:VKZJHPbIwGBnmWCslEFbtw==". Programmatic download is gated, so I downloaded the source manually from the website in its original CSV format ("countypres_2000-2024.csv"). The pipeline verifies the file's MD5 against the checksum published in the dataset's Dataverse metadata on every load.

### Cleaning

Upon downloading the data, I cleaned it as follows: I first filtered the file to the 2020 and 2016 US presidential races, keeping only Democratic and Republican votes. I dropped the non-county reporting units that carry no FIPS code, namely statewide write-ins, overseas/UOCAVA ballots, and Rhode Island's federal precinct. To ensure consistency with the rest of the data, I zero-padded the county FIPS codes to five-digit GEOIDs. I folded Kansas City's separately reported return (pseudo-FIPS 2938000) into Jackson County, MO to match census geography. I excluded Alaska because its returns are reported by election districts rather than by the census boroughs (county-equivalents) the national pipeline uses. I dropped the defunct Bedford City, VA, which merged into Bedford County in 2013 but remains in the file as a vestigial zero-vote 2016 row. Finally, I summed each county's votes, letting TOTAL rows take precedence over vote-mode splits because summing both would double-count. For the regression pipeline, the result is one row per county with four columns: Democratic and Republican presidential votes for 2020 and 2016.
