# Model variables

The 102 variables of the 11 model groups: 101 predictors the models use, and 1 kept for reference only. Each page lists a group's variables and, for each one, what it measures, where its numbers come from, and how they are combined.

| Group | Page | Variables |
|---|---|---|
| Language | [language.md](language.md) | 12 |
| US Citizenship and Residency Status | [citizenship.md](citizenship.md) | 3 |
| National Origin and Background | [national_origin.md](national_origin.md) | 17 |
| Mobility and Time in the U.S. | [mobility.md](mobility.md) | 18 |
| Education | [education.md](education.md) | 4 |
| Income and Affluence | [income.md](income.md) | 8 |
| Employment and Industry | [employment.md](employment.md) | 12 |
| Household Structure (Age, Marriage, Sex) | [household.md](household.md) | 11 |
| Racial and Ethnic Composition | [racial_ethnic.md](racial_ethnic.md) | 6 |
| Geography | [geography.md](geography.md) | 4 |
| Elections | [election.md](election.md) | 7 |

The outcomes the models predict, and the counts they are built from, are on their own page: [targets.md](targets.md).

## How to read a page

- **Variable name** is the column's name in the dataset files; the heading above it is the name used in tables and figures.
- **Role** says whether the models use the variable as an input (predictor) or whether it is kept only for reference (context).
- **How it is calculated** lists every input the variable reads. Census inputs are named by their official label, the table they come from, and their variable code (e.g. `B05003I_008E`), so any number can be looked up at data.census.gov. Codes ending in E are estimates.
- **Blank values.** A variable is left blank, never filled in or guessed, where an input is missing or a ratio's bottom number is zero. The ACS also marks some estimates as unavailable with special codes; those are treated as missing before any calculation.
- **Available for** says whether the variable is in both the county and the tract dataset or in the county dataset only.

## Sources

- **PL**: 2020 Decennial Census, P.L. 94-171 Redistricting file
- **ACS**: American Community Survey 5-year estimates, 2016-2020 (the growth variables also use 2011-2015)
- **DHC**: 2020 Decennial Census, Demographic and Housing Characteristics file
- **TIGER**: Census TIGER/Line 2020 shapefiles
- **ELECTION**: MGGG GerryDB release (presidential returns from Dave's Redistricting block data)
