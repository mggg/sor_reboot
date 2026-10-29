# The Feature Report

The feature report describes what is in processed.parquet before any model is fit on it (see [02_clean_derive_and_build.md](02_clean_derive_and_build.md) for how that file is built). For each column it is asked about, it draws a histogram and computes a row of descriptive statistics—how often the column is missing, where its values sit, and what shape they make—so that a reader can see, for example, that a share is zero in most counties, or that a variable has a long right tail, before interpreting anything a model says about it. The report fits nothing and changes nothing: it reads processed.parquet and writes one folder of figures and tables. What each variable means is written out in the [variable pages](variables/README.md); this document covers what the report does with them.

## Contents

- [Choosing Columns: Groups](#choosing-columns-groups)
- [Choosing Rows](#choosing-rows)
- [What the Report Writes](#what-the-report-writes)
- [The Statistics Table](#the-statistics-table)
- [Running the Report](#running-the-report)

## Choosing Columns: Groups

A report describes one or more groups of columns, named on the command line. There are two kinds:

- **A model group**: the predictors of one of the eleven thematic groups the regression is built from, followed by any context variable the group declares. Only the citizenship group has one: the citizen voting-age population, which is kept for reference rather than used as a predictor.
- **targets**: the four shares the regression predicts—of each unit's Hispanic residents, the share who chose Some Other Race alone, White and Some Other Race, White alone, and White alone or in combination.

| Group | Title | Counties | Tracts |
|---|---|---|---|
| language | Language | 12 | 12 |
| citizenship | US Citizenship and Residency Status | 2 + 1 context | 2 + 1 context |
| national_origin | National Origin and Background | 17 | 17 |
| mobility | Mobility and Time in the U.S. | 18 | 16 |
| education | Education | 4 | 4 |
| income | Income and Affluence | 8 | 8 |
| employment | Employment and Industry | 12 | 12 |
| household | Household Structure (Age, Marriage, Sex) | 11 | 11 |
| racial_ethnic | Racial and Ethnic Composition | 6 | 6 |
| geography | Geography | 4 | 4 |
| election | Elections | 7 | 6 |
| targets | The regression targets | 4 | 4 |

Asking for no group describes all eleven model groups; the targets are described only when named. The tract columns are the county columns minus the three the tract dataset leaves out: Hispanic population growth and foreign-born population growth (mobility) and voter turnout (election). The other columns of processed.parquet—the PL counts, the shares of the total population, and the dominant-race classification—are not reported: no model reads them, and their distributions mostly restate how large or how Hispanic a place is.

## Choosing Rows

The same column can be described over two different sets of rows, and the report asks which:

- **Complete-case** (the default): only the units the regression keeps, meaning those with every predictor and every target present. The rows are the same for every column, and they are the full model's rows whichever groups are being described, so a histogram here shows exactly the values a model fits on. With the current data, that is 2,912 of 3,221 counties and 58,767 of 85,395 tracts.
- **Available-case**: each column over every unit where that column is not blank. This is the truer picture of a variable on its own, but the rows differ from column to column, so two columns in the same report are no longer describing the same units.

In a complete-case report, the terminal also lists how many units each column cost, so the columns responsible for the dropped rows are visible. Whichever rows are chosen, the statistics table's missingness columns are always measured over every unit in the file, since inside the complete-case rows every column is present by construction.

## What the Report Writes

Each report writes one folder under data/report/features, named for the date, the geography, the groups, and the row choice, for example:

| Report | Folder |
|---|---|
| County election, complete-case | data/report/features/2026-10-29_counties_election |
| California tract targets, available-case | data/report/features/2026-10-29_tracts-CA_targets_available_case |

A report run twice on the same day with the same choices writes into the same folder, replacing its files. The folder holds four kinds of file:

| File | Contents |
|---|---|
| feature_stats.csv | One row of statistics per column, described below |
| hist_&lt;COLUMN&gt;.png | One histogram per column |
| distributions.png | Every column's histogram on one sheet, four across |
| README.md | What each statistic means, the geography and rows covered, and the list of columns described |

**Each histogram** is titled with the variable's name and the geography, then lists the variable's code, its description, the formula the build actually computed (for example, "Calculated as: hispanic or latino central american guatemalan / hispanic population"), and a line naming the geography and the rows covered. Where a variable is a share, its x-axis says what it is a share of, so a share of Hispanic residents cannot be mistaken for a share of everyone. Each histogram marks the median and the mean, which separate when a variable is skewed, and notes in its corner how many units it covers and what percentage sit at exactly zero. A formula that sums many census categories names the first few and counts the rest (for example, "male less than high school diploma + 1 more"); the variable pages list every input.

## The Statistics Table

feature_stats.csv has one row per column, in the order the groups were asked for. Every column other than the missingness ones is computed over the rows the report covers.

| Statistic | Meaning |
|---|---|
| n_rows_in_file | Every unit in processed.parquet, whether or not this column has a value there |
| n_rows_with_a_value | How many of those units have a value |
| pct_of_file_missing | The units without a value, as a percentage of the file |
| n_rows_in_this_report | How many units this report describes: the same for every column under complete-case, varying under available-case |
| mean | The average |
| weighted_mean | The average weighted by Hispanic population; a gap from the plain mean means the variable looks different where most Hispanic residents live |
| sd | Standard deviation |
| sd_over_mean | Standard deviation divided by the mean, for comparing spread across variables on different scales; blank where any value is negative or the mean is zero |
| min, max | Smallest and largest value |
| p5, q1, median, q3, p95 | The 5th, 25th, 50th, 75th, and 95th percentiles |
| range | max minus min |
| iqr | q3 minus q1, the width of the middle half |
| pct_zero | Percentage of units at exactly zero |
| pct_exactly_1 | Percentage of units at exactly 1; blank unless every value lies between 0 and 1 |
| skew | Asymmetry; positive means a long right tail |
| n_unique | Number of distinct values; far fewer than expected means the variable is nearly constant |
| spearman_with_Hisp_SOR_Alone_Pct_of_Hisp_Pop | Rank correlation with the share of Hispanic residents who chose Some Other Race alone |

The same explanations, in more detail, are written into each report's README.md.

## Running the Report

The report reads a processed.parquet that already exists, so the matching build must be run first. Every command runs from sor_pipeline_v2:

| To describe | Command |
|---|---|
| Every model group, all counties | `uv run python -m feature_report` |
| Some groups, all counties | `uv run python -m feature_report --groups language geography` |
| The targets, all tracts | `uv run python -m feature_report --level national_tracts --groups targets` |
| One group, tracts in some states | `uv run python -m feature_report --level national_tracts --states 06 --groups income` |

| Option | Values | Default |
|---|---|---|
| --level | national_counties, national_tracts | national_counties |
| --states | State FIPS codes, tracts only; reads the matching partial tract build | all states |
| --groups | Any of the group names above | every model group |
| --rows | complete_case, available_case | complete_case |
| --format | png, pdf, svg; pdf and svg stay sharp at any zoom | png |
| --dpi | Resolution of png figures, at least 300 | 300 |

The report checks every choice before reading any data, and stops with a one-line error naming the problem: an unknown group, state, or format, a resolution below 300, or states given for the county level, which has no state subsets.
