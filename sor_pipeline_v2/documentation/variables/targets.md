# Targets

The outcome side of the dataset: what the models predict, and the counts those outcomes are built from. Every column here comes from the 2020 Decennial Census PL file and is in both the county and the tract dataset. SOR stands for Some Other Race, one of the race categories on the census form. See [how to read these pages](README.md).

The regression predicts the 4 shares in the first section, weighting each county or tract by its Hispanic or Latino count (`HISPANIC`) so that places with more Hispanic residents count for more. On this page, Role says whether the regression predicts a column.

| Variable | Name | Predicted |
|---|---|---|
| SOR-alone share of Hispanic population | `Hisp_SOR_Alone_Pct_of_Hisp_Pop` | yes |
| White-and-SOR share of Hispanic population | `Hisp_White_SOR_Pct_of_Hisp_Pop` | yes |
| White-alone share of Hispanic population | `Hisp_White_Alone_Pct_of_Hisp_Pop` | yes |
| White alone-or-in-combination share of Hispanic population | `Hisp_White_Pct_of_Hisp_Pop` | yes |
| Hispanic share of total population | `Hisp_Pct_of_Total_Pop` | no |
| Hispanic SOR-alone share of total population | `Hisp_SOR_Alone_Pct_of_Total_Pop` | no |
| Hispanic White-and-SOR share of total population | `Hisp_White_SOR_Pct_of_Total_Pop` | no |
| Hispanic White-alone share of total population | `Hisp_White_Alone_Pct_of_Total_Pop` | no |
| Hispanic White alone-or-in-combination share of total population | `Hisp_White_Pct_of_Total_Pop` | no |
| Hispanic SOR-alone population | `HSOR` | no |
| Hispanic non-SOR population | `H_N_SOR` | no |
| Hispanic White-and-SOR population | `HWHITESOR` | no |
| Hispanic non-White-and-SOR population | `H_N_WHITESOR` | no |
| Hispanic White-alone population | `HWHITE` | no |
| Hispanic non-White-alone population | `H_N_WHITE` | no |
| Hispanic White alone-or-in-combination population | `HWHITEACOMBO` | no |
| Hispanic non-White-in-any-combination population | `H_N_WHITEACOMBO` | no |
| Total population | `TOTALPOP` | no |
| White alone | `WHITEALONE` | no |
| SOR alone | `SORALONE` | no |
| White and SOR | `WHITESOR` | no |
| Hispanic or Latino | `HISPANIC` | no |
| Non-Hispanic White alone | `NONHISPANICWHITEALONE` | no |
| Non-Hispanic SOR alone | `NONHISPANICSORALONE` | no |
| Non-Hispanic White and SOR | `NONHISPANICWHITESOR` | no |
| White alone or in combination | `WHITEALONEORCOMBO` | no |
| Non-Hispanic White alone or in combination | `NONHISPANICWHITEALONEORCOMBO` | no |
| Largest Hispanic race group | `largest` | no |
| Most Hispanic residents chose Some Other Race alone | `Most_SOR` | no |
| Most Hispanic residents chose White and Some Other Race | `Most_White_SOR` | no |
| Most Hispanic residents chose White alone | `Most_White` | no |

## What the models predict

### SOR-alone share of Hispanic population

| | |
|---|---|
| Variable name | `Hisp_SOR_Alone_Pct_of_Hisp_Pop` |
| Source | 2020 Decennial Census, P.L. 94-171 Redistricting file |
| Role | Predicted by the regression models |
| Available for | Counties and tracts |

**What it measures.** THE OUTCOME: share of Hispanic residents who selected Some Other Race alone

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** Hispanic SOR-alone population, itself a computed variable — `HSOR`

**Bottom (denominator):** Hispanic or Latino, itself a computed variable — `HISPANIC`

Left blank if any input is missing or the bottom number is zero.

### White-and-SOR share of Hispanic population

| | |
|---|---|
| Variable name | `Hisp_White_SOR_Pct_of_Hisp_Pop` |
| Source | 2020 Decennial Census, P.L. 94-171 Redistricting file |
| Role | Predicted by the regression models |
| Available for | Counties and tracts |

**What it measures.** THE OUTCOME: share of Hispanic residents who selected White and Some Other Race

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** Hispanic White-and-SOR population, itself a computed variable — `HWHITESOR`

**Bottom (denominator):** Hispanic or Latino, itself a computed variable — `HISPANIC`

Left blank if any input is missing or the bottom number is zero.

### White-alone share of Hispanic population

| | |
|---|---|
| Variable name | `Hisp_White_Alone_Pct_of_Hisp_Pop` |
| Source | 2020 Decennial Census, P.L. 94-171 Redistricting file |
| Role | Predicted by the regression models |
| Available for | Counties and tracts |

**What it measures.** THE OUTCOME: share of Hispanic residents who selected White alone

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** Hispanic White-alone population, itself a computed variable — `HWHITE`

**Bottom (denominator):** Hispanic or Latino, itself a computed variable — `HISPANIC`

Left blank if any input is missing or the bottom number is zero.

### White alone-or-in-combination share of Hispanic population

| | |
|---|---|
| Variable name | `Hisp_White_Pct_of_Hisp_Pop` |
| Source | 2020 Decennial Census, P.L. 94-171 Redistricting file |
| Role | Predicted by the regression models |
| Available for | Counties and tracts |

**What it measures.** Share of Hispanic residents who selected White alone or in any combination

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** Hispanic White alone-or-in-combination population, itself a computed variable — `HWHITEACOMBO`

**Bottom (denominator):** Hispanic or Latino, itself a computed variable — `HISPANIC`

Left blank if any input is missing or the bottom number is zero.

## Other outcome shares

### Hispanic share of total population

| | |
|---|---|
| Variable name | `Hisp_Pct_of_Total_Pop` |
| Source | 2020 Decennial Census, P.L. 94-171 Redistricting file |
| Role | Kept in the dataset for reference; not predicted by the regression |
| Available for | Counties and tracts |

**What it measures.** Hispanic population over total population, decennial

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** Hispanic or Latino, itself a computed variable — `HISPANIC`

**Bottom (denominator):** Total population, itself a computed variable — `TOTALPOP`

Left blank if any input is missing or the bottom number is zero.

### Hispanic SOR-alone share of total population

| | |
|---|---|
| Variable name | `Hisp_SOR_Alone_Pct_of_Total_Pop` |
| Source | 2020 Decennial Census, P.L. 94-171 Redistricting file |
| Role | Kept in the dataset for reference; not predicted by the regression |
| Available for | Counties and tracts |

**What it measures.** Hispanic SOR-alone population over total population

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** Hispanic SOR-alone population, itself a computed variable — `HSOR`

**Bottom (denominator):** Total population, itself a computed variable — `TOTALPOP`

Left blank if any input is missing or the bottom number is zero.

### Hispanic White-and-SOR share of total population

| | |
|---|---|
| Variable name | `Hisp_White_SOR_Pct_of_Total_Pop` |
| Source | 2020 Decennial Census, P.L. 94-171 Redistricting file |
| Role | Kept in the dataset for reference; not predicted by the regression |
| Available for | Counties and tracts |

**What it measures.** Hispanic White-and-SOR population over total population

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** Hispanic White-and-SOR population, itself a computed variable — `HWHITESOR`

**Bottom (denominator):** Total population, itself a computed variable — `TOTALPOP`

Left blank if any input is missing or the bottom number is zero.

### Hispanic White-alone share of total population

| | |
|---|---|
| Variable name | `Hisp_White_Alone_Pct_of_Total_Pop` |
| Source | 2020 Decennial Census, P.L. 94-171 Redistricting file |
| Role | Kept in the dataset for reference; not predicted by the regression |
| Available for | Counties and tracts |

**What it measures.** Hispanic White-alone population over total population

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** Hispanic White-alone population, itself a computed variable — `HWHITE`

**Bottom (denominator):** Total population, itself a computed variable — `TOTALPOP`

Left blank if any input is missing or the bottom number is zero.

### Hispanic White alone-or-in-combination share of total population

| | |
|---|---|
| Variable name | `Hisp_White_Pct_of_Total_Pop` |
| Source | 2020 Decennial Census, P.L. 94-171 Redistricting file |
| Role | Kept in the dataset for reference; not predicted by the regression |
| Available for | Counties and tracts |

**What it measures.** Hispanic White alone-or-in-combination population over total population

**How it is calculated.**

A ratio: the top number divided by the bottom number.

**Top (numerator):** Hispanic White alone-or-in-combination population, itself a computed variable — `HWHITEACOMBO`

**Bottom (denominator):** Total population, itself a computed variable — `TOTALPOP`

Left blank if any input is missing or the bottom number is zero.

## Hispanic-of-race counts

The PL file publishes no direct count of, for example, Hispanic residents who chose Some Other Race alone, so each count is computed as the count for everyone minus the count for non-Hispanic residents. Each share above divides one of these counts by the Hispanic or the total population.

### Hispanic SOR-alone population

| | |
|---|---|
| Variable name | `HSOR` |
| Source | 2020 Decennial Census, P.L. 94-171 Redistricting file |
| Role | Kept in the dataset for reference; not predicted by the regression |
| Available for | Counties and tracts |

**What it measures.** Hispanic residents who selected Some Other Race alone (all SOR-alone minus non-Hispanic SOR-alone)

**How it is calculated.**

One value minus another.

**Start from:** SOR alone, itself a computed variable — `SORALONE`

**Subtract:** Non-Hispanic SOR alone, itself a computed variable — `NONHISPANICSORALONE`

Left blank if either input is missing.

### Hispanic non-SOR population

| | |
|---|---|
| Variable name | `H_N_SOR` |
| Source | 2020 Decennial Census, P.L. 94-171 Redistricting file |
| Role | Kept in the dataset for reference; not predicted by the regression |
| Available for | Counties and tracts |

**What it measures.** Hispanic residents who did NOT select Some Other Race alone

**How it is calculated.**

One value minus another.

**Start from:** Hispanic or Latino, itself a computed variable — `HISPANIC`

**Subtract:** Hispanic SOR-alone population, itself a computed variable — `HSOR`

Left blank if either input is missing.

### Hispanic White-and-SOR population

| | |
|---|---|
| Variable name | `HWHITESOR` |
| Source | 2020 Decennial Census, P.L. 94-171 Redistricting file |
| Role | Kept in the dataset for reference; not predicted by the regression |
| Available for | Counties and tracts |

**What it measures.** Hispanic residents who selected White and Some Other Race (all White-SOR minus non-Hispanic White-SOR)

**How it is calculated.**

One value minus another.

**Start from:** White and SOR, itself a computed variable — `WHITESOR`

**Subtract:** Non-Hispanic White and SOR, itself a computed variable — `NONHISPANICWHITESOR`

Left blank if either input is missing.

### Hispanic non-White-and-SOR population

| | |
|---|---|
| Variable name | `H_N_WHITESOR` |
| Source | 2020 Decennial Census, P.L. 94-171 Redistricting file |
| Role | Kept in the dataset for reference; not predicted by the regression |
| Available for | Counties and tracts |

**What it measures.** Hispanic residents who did NOT select White and Some Other Race

**How it is calculated.**

One value minus another.

**Start from:** Hispanic or Latino, itself a computed variable — `HISPANIC`

**Subtract:** Hispanic White-and-SOR population, itself a computed variable — `HWHITESOR`

Left blank if either input is missing.

### Hispanic White-alone population

| | |
|---|---|
| Variable name | `HWHITE` |
| Source | 2020 Decennial Census, P.L. 94-171 Redistricting file |
| Role | Kept in the dataset for reference; not predicted by the regression |
| Available for | Counties and tracts |

**What it measures.** Hispanic residents who selected White alone (all White-alone minus non-Hispanic White-alone)

**How it is calculated.**

One value minus another.

**Start from:** White alone, itself a computed variable — `WHITEALONE`

**Subtract:** Non-Hispanic White alone, itself a computed variable — `NONHISPANICWHITEALONE`

Left blank if either input is missing.

### Hispanic non-White-alone population

| | |
|---|---|
| Variable name | `H_N_WHITE` |
| Source | 2020 Decennial Census, P.L. 94-171 Redistricting file |
| Role | Kept in the dataset for reference; not predicted by the regression |
| Available for | Counties and tracts |

**What it measures.** Hispanic residents who did NOT select White alone

**How it is calculated.**

One value minus another.

**Start from:** Hispanic or Latino, itself a computed variable — `HISPANIC`

**Subtract:** Hispanic White-alone population, itself a computed variable — `HWHITE`

Left blank if either input is missing.

### Hispanic White alone-or-in-combination population

| | |
|---|---|
| Variable name | `HWHITEACOMBO` |
| Source | 2020 Decennial Census, P.L. 94-171 Redistricting file |
| Role | Kept in the dataset for reference; not predicted by the regression |
| Available for | Counties and tracts |

**What it measures.** Hispanic residents who selected White alone or in any combination (all minus non-Hispanic)

**How it is calculated.**

One value minus another.

**Start from:** White alone or in combination, itself a computed variable — `WHITEALONEORCOMBO`

**Subtract:** Non-Hispanic White alone or in combination, itself a computed variable — `NONHISPANICWHITEALONEORCOMBO`

Left blank if either input is missing.

### Hispanic non-White-in-any-combination population

| | |
|---|---|
| Variable name | `H_N_WHITEACOMBO` |
| Source | 2020 Decennial Census, P.L. 94-171 Redistricting file |
| Role | Kept in the dataset for reference; not predicted by the regression |
| Available for | Counties and tracts |

**What it measures.** Hispanic residents who did NOT select White alone or in any combination

**How it is calculated.**

One value minus another.

**Start from:** Hispanic or Latino, itself a computed variable — `HISPANIC`

**Subtract:** Hispanic White alone-or-in-combination population, itself a computed variable — `HWHITEACOMBO`

Left blank if either input is missing.

## Dominant-race classification

These four columns are computed by hand-written code rather than a declared calculation, so they are described here in words.

### Largest Hispanic race group (`largest`)

| | |
|---|---|
| Variable name | `largest` |
| Source | 2020 Decennial Census, P.L. 94-171 Redistricting file |
| Role | Kept in the dataset for reference; not predicted by the regression |
| Available for | Counties and tracts |

**What it measures.** Which of three groups of Hispanic residents is largest: those who chose Some Other Race alone (coded 1), White and Some Other Race (coded 2), or White alone (coded 3).

**How it is calculated.**

The three counts are compared directly: Hispanic SOR-alone population (`HSOR`), Hispanic White-and-SOR population (`HWHITESOR`), Hispanic White-alone population (`HWHITE`). Comparing the shares instead would give the same answer, since all three divide by the same Hispanic population. Ties go to Some Other Race alone first, then to White alone, so a unit with no Hispanic residents, where all three counts are zero, is coded 1.

### Most Hispanic residents chose Some Other Race alone (`Most_SOR`)

1 where `largest` is 1, otherwise 0. Kept in the dataset for reference; not predicted by the regression; available for counties and tracts.

### Most Hispanic residents chose White and Some Other Race (`Most_White_SOR`)

1 where `largest` is 2, otherwise 0. Kept in the dataset for reference; not predicted by the regression; available for counties and tracts.

### Most Hispanic residents chose White alone (`Most_White`)

1 where `largest` is 3, otherwise 0. Kept in the dataset for reference; not predicted by the regression; available for counties and tracts.

## Population counts

Taken or summed directly from the PL tables; every column above is computed from these.

### Total population

| | |
|---|---|
| Variable name | `TOTALPOP` |
| Source | 2020 Decennial Census, P.L. 94-171 Redistricting file |
| Role | Kept in the dataset for reference; not predicted by the regression |
| Available for | Counties and tracts |

**What it measures.** Total population

**How it is calculated.**

Taken directly from Total — `P1_001N`, PL table P1: Race.

### White alone

| | |
|---|---|
| Variable name | `WHITEALONE` |
| Source | 2020 Decennial Census, P.L. 94-171 Redistricting file |
| Role | Kept in the dataset for reference; not predicted by the regression |
| Available for | Counties and tracts |

**What it measures.** White alone

**How it is calculated.**

Taken directly from White alone — `P1_003N`, PL table P1: Race.

### SOR alone

| | |
|---|---|
| Variable name | `SORALONE` |
| Source | 2020 Decennial Census, P.L. 94-171 Redistricting file |
| Role | Kept in the dataset for reference; not predicted by the regression |
| Available for | Counties and tracts |

**What it measures.** Some Other Race alone

**How it is calculated.**

Taken directly from Some other race alone — `P1_008N`, PL table P1: Race.

### White and SOR

| | |
|---|---|
| Variable name | `WHITESOR` |
| Source | 2020 Decennial Census, P.L. 94-171 Redistricting file |
| Role | Kept in the dataset for reference; not predicted by the regression |
| Available for | Counties and tracts |

**What it measures.** White; Some Other Race

**How it is calculated.**

Taken directly from White some other race — `P1_015N`, PL table P1: Race.

### Hispanic or Latino

| | |
|---|---|
| Variable name | `HISPANIC` |
| Source | 2020 Decennial Census, P.L. 94-171 Redistricting file |
| Role | Kept in the dataset for reference; not predicted by the regression |
| Available for | Counties and tracts |

**What it measures.** Hispanic or Latino

**How it is calculated.**

Taken directly from Hispanic or Latino — `P2_002N`, PL table P2: Hispanic or Latino, and not Hispanic or Latino by race.

### Non-Hispanic White alone

| | |
|---|---|
| Variable name | `NONHISPANICWHITEALONE` |
| Source | 2020 Decennial Census, P.L. 94-171 Redistricting file |
| Role | Kept in the dataset for reference; not predicted by the regression |
| Available for | Counties and tracts |

**What it measures.** Not Hispanic or Latino: White alone

**How it is calculated.**

Taken directly from Not Hispanic or Latino white alone — `P2_005N`, PL table P2: Hispanic or Latino, and not Hispanic or Latino by race.

### Non-Hispanic SOR alone

| | |
|---|---|
| Variable name | `NONHISPANICSORALONE` |
| Source | 2020 Decennial Census, P.L. 94-171 Redistricting file |
| Role | Kept in the dataset for reference; not predicted by the regression |
| Available for | Counties and tracts |

**What it measures.** Not Hispanic or Latino: Some Other Race alone

**How it is calculated.**

Taken directly from Not Hispanic or Latino some other race alone — `P2_010N`, PL table P2: Hispanic or Latino, and not Hispanic or Latino by race.

### Non-Hispanic White and SOR

| | |
|---|---|
| Variable name | `NONHISPANICWHITESOR` |
| Source | 2020 Decennial Census, P.L. 94-171 Redistricting file |
| Role | Kept in the dataset for reference; not predicted by the regression |
| Available for | Counties and tracts |

**What it measures.** Not Hispanic or Latino: White; Some Other Race

**How it is calculated.**

Taken directly from Not Hispanic or Latino white some other race — `P2_017N`, PL table P2: Hispanic or Latino, and not Hispanic or Latino by race.

### White alone or in combination

| | |
|---|---|
| Variable name | `WHITEALONEORCOMBO` |
| Source | 2020 Decennial Census, P.L. 94-171 Redistricting file |
| Role | Kept in the dataset for reference; not predicted by the regression |
| Available for | Counties and tracts |

**What it measures.** White alone or in combination with one or more other races

**How it is calculated.**

The sum of:

- White alone — `P1_003N`, PL table P1: Race
- White black or African American — `P1_011N`, PL table P1: Race
- White American indian and Alaska Native — `P1_012N`, PL table P1: Race
- White Asian — `P1_013N`, PL table P1: Race
- White native hawaiian and other pacific islander — `P1_014N`, PL table P1: Race
- White some other race — `P1_015N`, PL table P1: Race
- White black or African American American indian and Alaska Native — `P1_027N`, PL table P1: Race
- White black or African American Asian — `P1_028N`, PL table P1: Race
- White black or African American native hawaiian and other pacific islander — `P1_029N`, PL table P1: Race
- White black or African American some other race — `P1_030N`, PL table P1: Race
- White American indian and Alaska Native Asian — `P1_031N`, PL table P1: Race
- White American indian and Alaska Native native hawaiian and other pacific islander — `P1_032N`, PL table P1: Race
- White American indian and Alaska Native some other race — `P1_033N`, PL table P1: Race
- White Asian native hawaiian and other pacific islander — `P1_034N`, PL table P1: Race
- White Asian some other race — `P1_035N`, PL table P1: Race
- White native hawaiian and other pacific islander some other race — `P1_036N`, PL table P1: Race
- White black or African American American indian and Alaska Native Asian — `P1_048N`, PL table P1: Race
- White black or African American American indian and Alaska Native native hawaiian and other pacific islander — `P1_049N`, PL table P1: Race
- White black or African American American indian and Alaska Native some other race — `P1_050N`, PL table P1: Race
- White black or African American Asian native hawaiian and other pacific islander — `P1_051N`, PL table P1: Race
- White black or African American Asian some other race — `P1_052N`, PL table P1: Race
- White black or African American native hawaiian and other pacific islander some other race — `P1_053N`, PL table P1: Race
- White American indian and Alaska Native Asian native hawaiian and other pacific islander — `P1_054N`, PL table P1: Race
- White American indian and Alaska Native Asian some other race — `P1_055N`, PL table P1: Race
- White American indian and Alaska Native native hawaiian and other pacific islander some other race — `P1_056N`, PL table P1: Race
- White Asian native hawaiian and other pacific islander some other race — `P1_057N`, PL table P1: Race
- White black or African American American indian and Alaska Native Asian native hawaiian and other pacific islander — `P1_064N`, PL table P1: Race
- White black or African American American indian and Alaska Native Asian some other race — `P1_065N`, PL table P1: Race
- White black or African American American indian and Alaska Native native hawaiian and other pacific islander some other race — `P1_066N`, PL table P1: Race
- White black or African American Asian native hawaiian and other pacific islander some other race — `P1_067N`, PL table P1: Race
- White American indian and Alaska Native Asian native hawaiian and other pacific islander some other race — `P1_068N`, PL table P1: Race
- White black or African American American indian and Alaska Native Asian native hawaiian and other pacific islander some other race — `P1_071N`, PL table P1: Race

Left blank if any input is missing.

### Non-Hispanic White alone or in combination

| | |
|---|---|
| Variable name | `NONHISPANICWHITEALONEORCOMBO` |
| Source | 2020 Decennial Census, P.L. 94-171 Redistricting file |
| Role | Kept in the dataset for reference; not predicted by the regression |
| Available for | Counties and tracts |

**What it measures.** Not Hispanic or Latino: White alone or in combination with one or more other races

**How it is calculated.**

The sum of:

- Not Hispanic or Latino white alone — `P2_005N`, PL table P2: Hispanic or Latino, and not Hispanic or Latino by race
- Not Hispanic or Latino white black or African American — `P2_013N`, PL table P2: Hispanic or Latino, and not Hispanic or Latino by race
- Not Hispanic or Latino white American indian and Alaska Native — `P2_014N`, PL table P2: Hispanic or Latino, and not Hispanic or Latino by race
- Not Hispanic or Latino white Asian — `P2_015N`, PL table P2: Hispanic or Latino, and not Hispanic or Latino by race
- Not Hispanic or Latino white native hawaiian and other pacific islander — `P2_016N`, PL table P2: Hispanic or Latino, and not Hispanic or Latino by race
- Not Hispanic or Latino white some other race — `P2_017N`, PL table P2: Hispanic or Latino, and not Hispanic or Latino by race
- Not Hispanic or Latino white black or African American American indian and Alaska Native — `P2_029N`, PL table P2: Hispanic or Latino, and not Hispanic or Latino by race
- Not Hispanic or Latino white black or African American Asian — `P2_030N`, PL table P2: Hispanic or Latino, and not Hispanic or Latino by race
- Not Hispanic or Latino white black or African American native hawaiian and other pacific islander — `P2_031N`, PL table P2: Hispanic or Latino, and not Hispanic or Latino by race
- Not Hispanic or Latino white black or African American some other race — `P2_032N`, PL table P2: Hispanic or Latino, and not Hispanic or Latino by race
- Not Hispanic or Latino white American indian and Alaska Native Asian — `P2_033N`, PL table P2: Hispanic or Latino, and not Hispanic or Latino by race
- Not Hispanic or Latino white American indian and Alaska Native native hawaiian and other pacific islander — `P2_034N`, PL table P2: Hispanic or Latino, and not Hispanic or Latino by race
- Not Hispanic or Latino white American indian and Alaska Native some other race — `P2_035N`, PL table P2: Hispanic or Latino, and not Hispanic or Latino by race
- Not Hispanic or Latino white Asian native hawaiian and other pacific islander — `P2_036N`, PL table P2: Hispanic or Latino, and not Hispanic or Latino by race
- Not Hispanic or Latino white Asian some other race — `P2_037N`, PL table P2: Hispanic or Latino, and not Hispanic or Latino by race
- Not Hispanic or Latino white native hawaiian and other pacific islander some other race — `P2_038N`, PL table P2: Hispanic or Latino, and not Hispanic or Latino by race
- Not Hispanic or Latino white black or African American American indian and Alaska Native Asian — `P2_050N`, PL table P2: Hispanic or Latino, and not Hispanic or Latino by race
- Not Hispanic or Latino white black or African American American indian and Alaska Native native hawaiian and other pacific islander — `P2_051N`, PL table P2: Hispanic or Latino, and not Hispanic or Latino by race
- Not Hispanic or Latino white black or African American American indian and Alaska Native some other race — `P2_052N`, PL table P2: Hispanic or Latino, and not Hispanic or Latino by race
- Not Hispanic or Latino white black or African American Asian native hawaiian and other pacific islander — `P2_053N`, PL table P2: Hispanic or Latino, and not Hispanic or Latino by race
- Not Hispanic or Latino white black or African American Asian some other race — `P2_054N`, PL table P2: Hispanic or Latino, and not Hispanic or Latino by race
- Not Hispanic or Latino white black or African American native hawaiian and other pacific islander some other race — `P2_055N`, PL table P2: Hispanic or Latino, and not Hispanic or Latino by race
- Not Hispanic or Latino white American indian and Alaska Native Asian native hawaiian and other pacific islander — `P2_056N`, PL table P2: Hispanic or Latino, and not Hispanic or Latino by race
- Not Hispanic or Latino white American indian and Alaska Native Asian some other race — `P2_057N`, PL table P2: Hispanic or Latino, and not Hispanic or Latino by race
- Not Hispanic or Latino white American indian and Alaska Native native hawaiian and other pacific islander some other race — `P2_058N`, PL table P2: Hispanic or Latino, and not Hispanic or Latino by race
- Not Hispanic or Latino white Asian native hawaiian and other pacific islander some other race — `P2_059N`, PL table P2: Hispanic or Latino, and not Hispanic or Latino by race
- Not Hispanic or Latino white black or African American American indian and Alaska Native Asian native hawaiian and other pacific islander — `P2_066N`, PL table P2: Hispanic or Latino, and not Hispanic or Latino by race
- Not Hispanic or Latino white black or African American American indian and Alaska Native Asian some other race — `P2_067N`, PL table P2: Hispanic or Latino, and not Hispanic or Latino by race
- Not Hispanic or Latino white black or African American American indian and Alaska Native native hawaiian and other pacific islander some other race — `P2_068N`, PL table P2: Hispanic or Latino, and not Hispanic or Latino by race
- Not Hispanic or Latino white black or African American Asian native hawaiian and other pacific islander some other race — `P2_069N`, PL table P2: Hispanic or Latino, and not Hispanic or Latino by race
- Not Hispanic or Latino white American indian and Alaska Native Asian native hawaiian and other pacific islander some other race — `P2_070N`, PL table P2: Hispanic or Latino, and not Hispanic or Latino by race
- Not Hispanic or Latino white black or African American American indian and Alaska Native Asian native hawaiian and other pacific islander some other race — `P2_073N`, PL table P2: Hispanic or Latino, and not Hispanic or Latino by race

Left blank if any input is missing.
