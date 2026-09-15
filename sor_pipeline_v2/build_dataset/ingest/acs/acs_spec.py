"""Declarative spec for the ACS 5-year predictor feature set.

Single source of truth for two things that must never drift apart:

  1. which raw ACS columns get fetched (`estimate_codes` / `moe_codes`),
  2. how each modeled ACS feature is built from them (`iter_features`).

ACS ONLY. The other sources declare their own features (`dhc.py`,
`geometry.py`, `election.py`), and the thematic model groups spanning all
sources live in `build_dataset/manifest.py`, which imports from every source
and asserts the partition at import time.

Design rule: every count feature is a share of ITS OWN table's published
universe, named explicitly in `Feature.denominator`. There is no global
denominator. This is what prevents the class of bug where an origin count was
divided by total population instead of by the Hispanic population.

Tables whose name ends in `I` are the Hispanic-or-Latino iteration: the universe
is already restricted to Hispanic respondents, matching the universe the outcome
is measured over. Tables without the suffix cover the whole population and are
marked `hispanic_universe=False`.

Sections mirror the manifest's model-group letters: section A holds exactly the
ACS features of group A, and so on. Groups J (geography) and K (elections) have
no section because their features are not ACS tables. A table whose features
span two groups appears once per group with the relevant subset
(`estimate_codes` deduplicates, so the fetch is unaffected).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Feature:
    """One modeled feature: a numerator over a denominator, both within one table.

    `numerator` and `denominator` are bare line numbers (e.g. "003"); the table
    prefix and the `E` suffix are added by the `*_codes` properties. A feature
    with an empty denominator is not a share (a median), and passes through
    unchanged.

    Multiple numerator lines are SUMMED. This is how the sex-split tables
    (C15002I, C24010I, C24030, B05003I, C23002I, B01001I) are collapsed to
    totals: those tables publish no combined line for each category, so male and
    female must be added. Their margins of error are combined in quadrature, not
    added, in the clean stage.
    """

    name: str
    table: str
    numerator: tuple[str, ...]
    denominator: tuple[str, ...]
    meaning: str
    # Set only where the denominator is a SUBTOTAL rather than the table total,
    # so the feature's universe differs from the table's. Reporting the table
    # universe in those cases misstates what the share is a share of.
    universe: str = ""

    @property
    def numerator_codes(self) -> tuple[str, ...]:
        return tuple(f"{self.table}_{line}E" for line in self.numerator)

    @property
    def denominator_codes(self) -> tuple[str, ...]:
        return tuple(f"{self.table}_{line}E" for line in self.denominator)

    @property
    def is_share(self) -> bool:
        return bool(self.denominator)


@dataclass(frozen=True)
class TableSpec:
    """One ACS table and the features drawn from it (within one section)."""

    table: str
    universe: str
    hispanic_universe: bool
    features: tuple[Feature, ...]


@dataclass(frozen=True)
class Section:
    """The ACS features of one model group, keyed by the same letter."""

    letter: str
    title: str
    tables: tuple[TableSpec, ...] = field(default_factory=tuple)


def _f(name, table, numerator, denominator, meaning, universe="") -> Feature:
    """Terser Feature constructor; splits whitespace-separated line lists."""
    return Feature(
        name=name,
        table=table,
        numerator=tuple(numerator.split()),
        denominator=tuple(denominator.split()) if denominator else (),
        meaning=meaning,
        universe=universe,
    )


HISP = "Hispanic or Latino population"

# ---------------------------------------------------------------------------
# A. Language
# ---------------------------------------------------------------------------
# The six nativity x language cross-tabs sit here rather than under mobility:
# they measure English ability, conditioned on nativity.
_A = Section("A", "Language", (
    TableSpec("B16006", f"{HISP} 5 years and over", True, (
        _f("HISPENGONLY", "B16006", "002", "001",
           "Hispanics who speak only English at home"),
        _f("HISPSPANVERYWELL", "B16006", "004", "001",
           'Spanish speakers who report speaking English "very well"'),
        _f("HISPSPANWELL", "B16006", "005", "001",
           'Spanish speakers who report speaking English "well"'),
        _f("HISPSPANNOTWELL", "B16006", "006", "001",
           'Spanish speakers who report speaking English "not well"'),
        _f("HISPSPANNOTATALL", "B16006", "007", "001",
           'Spanish speakers who report speaking English "not at all"'),
        _f("HISPOTHERLANG", "B16006", "008", "001",
           "Hispanics who speak a language other than English or Spanish at home"),
    )),
    TableSpec("B16005I", f"{HISP} 5 years and over", True, (
        _f("HISPNATIVEENGONLY", "B16005I", "003", "001",
           'Native-born Hispanics who speak only English at home'),
        _f("HISPNATIVEOTHERVW", "B16005I", "005", "001",
           'Native-born Hispanics who speak another language and English "very well"'),
        _f("HISPNATIVEOTHERLTVW", "B16005I", "006", "001",
           'Native-born Hispanics who speak another language and English less than "very well"'),
        _f("HISPFBENGONLY", "B16005I", "008", "001",
           'Foreign-born Hispanics who speak only English at home'),
        _f("HISPFBOTHERVW", "B16005I", "010", "001",
           'Foreign-born Hispanics who speak another language and English "very well"'),
        _f("HISPFBOTHERLTVW", "B16005I", "011", "001",
           'Foreign-born Hispanics who speak another language and English less than "very well"'),
    )),
))

# ---------------------------------------------------------------------------
# B. US Citizenship and Residency Status
# ---------------------------------------------------------------------------
# B05003I is split between this section and D (mobility): citizenship status
# here, foreign-born shares there. Same table, disjoint feature subsets.
#
# Denominators here are deliberately the age subtotals, not the table total:
# "of Hispanic ADULTS, what fraction are naturalized". Dividing by the whole
# Hispanic population would let a county's age structure masquerade as
# citizenship status.
_B = Section("B", "US Citizenship and Residency Status", (
    TableSpec("B05003I", HISP, True, (
        _f("HISPADULTNATURALIZED", "B05003I", "011 022", "008 019",
           "Share of Hispanic adults (18+) who are naturalized U.S. citizens",
           universe="Hispanic or Latino population 18 years and over"),
        _f("HISPADULTNONCITIZEN", "B05003I", "012 023", "008 019",
           "Share of Hispanic adults (18+) who are not U.S. citizens",
           universe="Hispanic or Latino population 18 years and over"),
    )),
))

# ---------------------------------------------------------------------------
# C. National Origin and Background
# ---------------------------------------------------------------------------
# Denominator is B03001_003E, the table's "Hispanic or Latino" row -- NOT _001E,
# which is the table's total-population row. Using _001E was the original bug.
_C = Section("C", "National Origin and Background", (
    # B03001 is NESTED, not a flat list. Seven top-level rows partition the
    # Hispanic population exactly:
    #
    #     _004 Mexican  _005 Puerto Rican  _006 Cuban  _007 Dominican
    #     _008 Central American (all)   _016 South American (all)
    #     _027 Other Hispanic (all)
    #
    # and three of those break down further. The meanings below say which rows
    # are totals and which sit inside them, because summing a total together
    # with its own components double-counts.
    TableSpec("B03001", HISP, True, (
        _f("MEXICANORIGIN", "B03001", "004", "003",
           "Mexican origin. Top-level category; 58% of US Hispanics."),
        _f("PUERTORICANORIGIN", "B03001", "005", "003",
           "Puerto Rican origin. Top-level category."),
        _f("CUBANORIGIN", "B03001", "006", "003",
           "Cuban origin. Top-level category."),
        _f("DOMINICANORIGIN", "B03001", "007", "003",
           "Dominican (Dominican Republic) origin. Top-level category."),
        _f("CENTRALAMORIGIN", "B03001", "008", "003",
           "Central American origin, TOTAL across all countries. Contains the "
           "Guatemalan, Honduran and Salvadoran features below, plus Costa "
           "Rican, Nicaraguan and Panamanian, which are not modeled."),
        _f("GUATEMALANORIGIN", "B03001", "010", "003",
           "Guatemalan origin. A subset of CENTRALAMORIGIN, not additional to it."),
        _f("HONDURANORIGIN", "B03001", "011", "003",
           "Honduran origin. A subset of CENTRALAMORIGIN, not additional to it."),
        _f("SALVADORANORIGIN", "B03001", "014", "003",
           "Salvadoran origin. A subset of CENTRALAMORIGIN, not additional to it."),
        _f("SOUTHAMORIGIN", "B03001", "016", "003",
           "South American origin, TOTAL across all countries. Contains the "
           "Colombian, Ecuadorian, Peruvian and Venezuelan features below, plus "
           "six smaller nationalities that are not modeled."),
        _f("COLOMBIANORIGIN", "B03001", "020", "003",
           "Colombian origin. A subset of SOUTHAMORIGIN, not additional to it."),
        _f("ECUADORIANORIGIN", "B03001", "021", "003",
           "Ecuadorian origin. A subset of SOUTHAMORIGIN, not additional to it."),
        _f("PERUVIANORIGIN", "B03001", "023", "003",
           "Peruvian origin. A subset of SOUTHAMORIGIN, not additional to it."),
        _f("VENEZUELANORIGIN", "B03001", "025", "003",
           "Venezuelan origin. A subset of SOUTHAMORIGIN, not additional to it."),
        _f("OTHERORIGINTOTAL", "B03001", "027", "003",
           "Other Hispanic or Latino, TOTAL: everyone whose reported origin is "
           "not Mexican, Puerto Rican, Cuban, Dominican, Central American or "
           "South American. 5.5% of US Hispanics. Contains the two features "
           "below."),
        _f("SPANIARDORIGIN", "B03001", "028", "003",
           "Spaniard (origin in Spain). A subset of OTHERORIGINTOTAL."),
        _f("HISPORIGINUNSPECIFIED", "B03001", "031", "003",
           "Reported a Hispanic or Latino identity but no specific national "
           "origin: write-ins such as \"Hispanic\", \"Latino\" or \"Latin "
           "American\", plus origins too small for the Census to tabulate "
           "separately. A subset of OTHERORIGINTOTAL, and 57% of it. "
           "1.95 million people, 3.1% of US Hispanics."),
    )),
    # FBLATAMSHARE is origin (where the foreign born are from); the rest of
    # B05002 sits under D (mobility). Same table, disjoint feature subsets.
    TableSpec("B05002", "Total population", False, (
        _f("FBLATAMSHARE", "B05002", "019 026", "013",
           "Of the foreign born, the share born in Latin America (naturalized "
           "plus non-citizen)",
           universe="Foreign-born population"),
    )),
))

# ---------------------------------------------------------------------------
# D. Mobility and Time in the U.S.
# ---------------------------------------------------------------------------
# Also home to the growth features (`GROWTH_FEATURES`, declared separately
# below because they compare two ACS vintages rather than reading one table):
# population change as in-migration.
_D = Section("D", "Mobility and Time in the U.S.", (
    # The foreign-born half of B05003I; citizenship status is in section B.
    # Denominators are the age subtotals, not the table total -- see section B.
    TableSpec("B05003I", HISP, True, (
        _f("HISPADULTFB", "B05003I", "010 021", "008 019",
           "Share of Hispanic adults (18+) who are foreign born",
           universe="Hispanic or Latino population 18 years and over"),
        _f("HISPCHILDFB", "B05003I", "005 016", "003 014",
           "Share of Hispanic children (under 18) who are foreign born",
           universe="Hispanic or Latino population under 18 years"),
    )),
    # Whole-county immigrant presence: "is this an immigrant gateway county".
    # Distinct from HISPADULTFB, which is a property of Hispanic residents; this
    # is a property of the place. The predecessor of this feature (FOREIGNBORN,
    # as a raw count) ranked 2nd in the weighted county models.
    #
    # PRBORNSHARE is mobility on purpose: island-born Puerto Ricans are migrants
    # the foreign-born measures cannot see, though citizens by birth.
    TableSpec("B05002", "Total population", False, (
        _f("FOREIGNBORNSHARE", "B05002", "013", "001",
           "Share of the total population that is foreign born"),
        _f("PRBORNSHARE", "B05002", "010", "001",
           "Share of the total population born in Puerto Rico (native-born, so "
           "invisible to every foreign-born measure)"),
    )),
    # No `I` iteration exists for year of entry: whole-population only.
    #
    # The denominator is the four foreign-born cohort lines summed, NOT the
    # table total `_001E`. `_001E` is the population WITH A PERIOD OF ENTRY --
    # foreign born plus natives born outside the U.S. -- not total population,
    # and it runs 8-13% of a county's population. Verified against B05002_013E:
    # `_004 + _009 + _014 + _019` equals the foreign-born count exactly.
    #
    # Dividing by the cohort sum makes these a pure COMPOSITION of the
    # foreign-born population ("of immigrants here, what share arrived since
    # 2010"), which sums to 1 and is not confounded with how immigrant-heavy the
    # county is. The level is already carried separately by FOREIGNBORNSHARE
    # and, on the Hispanic universe, by HISPADULTFB.
    TableSpec("B05005", "Foreign-born population (period of entry known)", False, (
        _f("FBENTERED2010PLUS", "B05005", "004", "004 009 014 019",
           "Of the foreign born, the share who entered the U.S. in 2010 or later",
           universe="Foreign-born population (period of entry known)"),
        _f("FBENTERED2000S", "B05005", "009", "004 009 014 019",
           "Of the foreign born, the share who entered the U.S. 2000-2009",
           universe="Foreign-born population (period of entry known)"),
        _f("FBENTERED1990S", "B05005", "014", "004 009 014 019",
           "Of the foreign born, the share who entered the U.S. 1990-1999",
           universe="Foreign-born population (period of entry known)"),
        _f("FBENTEREDPRE1990", "B05005", "019", "004 009 014 019",
           "Of the foreign born, the share who entered the U.S. before 1990",
           universe="Foreign-born population (period of entry known)"),
    )),
    # B05007 publishes no combined Latin America x period line, so each period
    # sums its four subregion lines: Caribbean, Mexico, Other Central America,
    # South America.
    TableSpec("B05007", "Foreign-born population", False, (
        _f("LATAMFBENTERED2010PLUS", "B05007", "042 056 069 082", "040",
           "Of the Latin-American foreign born, the share who entered the "
           "U.S. in 2010 or later",
           universe="Foreign-born population born in Latin America"),
        _f("LATAMFBENTERED2000S", "B05007", "045 059 072 085", "040",
           "Of the Latin-American foreign born, the share who entered the "
           "U.S. 2000-2009",
           universe="Foreign-born population born in Latin America"),
        _f("LATAMFBENTERED1990S", "B05007", "048 062 075 088", "040",
           "Of the Latin-American foreign born, the share who entered the "
           "U.S. 1990-1999",
           universe="Foreign-born population born in Latin America"),
        _f("LATAMFBENTEREDPRE1990", "B05007", "051 065 078 091", "040",
           "Of the Latin-American foreign born, the share who entered the "
           "U.S. before 1990",
           universe="Foreign-born population born in Latin America"),
    )),
    TableSpec("B07004I", f"{HISP} 1 year and over", True, (
        _f("HISPMOVEDWITHINCOUNTY", "B07004I", "003", "001",
           "Moved within the same county in the past year"),
        _f("HISPMOVEDDIFFCOUNTY", "B07004I", "004", "001",
           "Moved from a different county in the same state"),
        _f("HISPMOVEDDIFFSTATE", "B07004I", "005", "001",
           "Moved from a different state"),
        _f("HISPMOVEDABROAD", "B07004I", "006", "001",
           "Moved from abroad in the past year"),
    )),
))

# ---------------------------------------------------------------------------
# E. Education
# ---------------------------------------------------------------------------
_E = Section("E", "Education", (
    TableSpec("C15002I", f"{HISP} 25 years and over", True, (
        _f("HISPEDULTHS", "C15002I", "003 008", "001",
           "Less than a high school diploma"),
        _f("HISPEDUHS", "C15002I", "004 009", "001",
           "High school graduate or equivalency"),
        _f("HISPEDUSOMECOLL", "C15002I", "005 010", "001",
           "Some college or an associate's degree"),
        _f("HISPEDUBAPLUS", "C15002I", "006 011", "001",
           "Bachelor's degree or higher"),
    )),
))

# ---------------------------------------------------------------------------
# F. Income and Affluence
# ---------------------------------------------------------------------------
# The computer/broadband trio is income on purpose: material-resource proxies.
_F = Section("F", "Income and Affluence", (
    TableSpec("B19301I", HISP, True, (
        _f("HISPPERCAPINCOME", "B19301I", "001", "",
           "Per capita income, Hispanic population (2020 dollars)"),
    )),
    # B19013I (median household income, Hispanic householder) is EXCLUDED from
    # the model. The Census will not compute a median where there are too few
    # Hispanic-householder households, so it is missing in exactly the small-
    # Hispanic counties -- and because a forest rejects NaN, each of those
    # counties was dropped entirely. It was the sole cause of 515 dropped rows,
    # 21% of the sample, to add one income measure that HISPPERCAPINCOME already
    # largely covers. Removing the feature also removes B19013I_001E from the
    # fetch; restore both by uncommenting the TableSpec below.
    #
    # TableSpec("B19013I", "Households with a Hispanic or Latino householder", True, (
    #     _f("HISPMEDINCOME", "B19013I", "001", "",
    #        "Median household income, Hispanic householder (2020 dollars)"),
    # )),
    TableSpec("B17001I", f"{HISP} for whom poverty status is determined", True, (
        _f("HISPPOVERTY", "B17001I", "002", "001",
           "Income in the past 12 months below the poverty level"),
    )),
    TableSpec("B22005I", "Households with a Hispanic or Latino householder", True, (
        _f("HISPSNAP", "B22005I", "002", "001",
           "Received SNAP/Food Stamps in the past 12 months"),
    )),
    TableSpec("B25003I", "Occupied housing units with a Hispanic or Latino householder", True, (
        _f("HISPOWNEROCC", "B25003I", "002", "001",
           "Owner-occupied (renter-occupied is the exact complement)"),
    )),
    TableSpec("B25014I", "Occupied housing units with a Hispanic or Latino householder", True, (
        _f("HISPCROWDING", "B25014I", "003", "001",
           "Crowded housing: 1.01 or more occupants per room"),
    )),
    # Replaces the old whole-population NOINTERNET (B28002_013E, all households).
    # The three lines below partition the table: broadband, a computer without
    # broadband (dial-up only or no subscription), and no computer at all.
    TableSpec("B28009I", "Households with a Hispanic or Latino householder", True, (
        _f("HISPBROADBAND", "B28009I", "004", "001",
           "Has a computer with a broadband internet subscription"),
        _f("HISPCOMPUTERNOBROADBAND", "B28009I", "003 005", "001",
           "Has a computer but no broadband (dial-up only, or no subscription)"),
        _f("HISPNOCOMPUTER", "B28009I", "006", "001", "No computer in the household"),
    )),
))

# ---------------------------------------------------------------------------
# G. Employment and Industry
# ---------------------------------------------------------------------------
_G = Section("G", "Employment and Industry", (
    TableSpec("C24010I", f"Civilian employed {HISP} 16 years and over", True, (
        _f("HISPOCCMGMT", "C24010I", "003 009", "001",
           "Management, business, science, and arts occupations"),
        _f("HISPOCCSERVICE", "C24010I", "004 010", "001", "Service occupations"),
        _f("HISPOCCSALESOFFICE", "C24010I", "005 011", "001",
           "Sales and office occupations"),
        _f("HISPOCCNATRESCONST", "C24010I", "006 012", "001",
           "Natural resources, construction, and maintenance occupations"),
        _f("HISPOCCPRODTRANS", "C24010I", "007 013", "001",
           "Production, transportation, and material moving occupations"),
    )),
    # Industry is published only for the whole civilian employed population -- the
    # `I` iteration covers occupation (C24010I), not industry. These five are
    # therefore LOCAL LABOUR-MARKET CONTEXT ("this is an agricultural county"),
    # not a characteristic of Hispanic residents. The memo must say so.
    TableSpec("C24030", "Civilian employed population 16 years and over", False, (
        _f("INDAGRICULTURE", "C24030", "004 031", "001",
           "Employed in agriculture, forestry, fishing and hunting"),
        _f("INDCONSTRUCTION", "C24030", "006 033", "001", "Employed in construction"),
        _f("INDMANUFACTURING", "C24030", "007 034", "001", "Employed in manufacturing"),
        _f("INDEDUHEALTH", "C24030", "021 048", "001",
           "Employed in educational services, health care, and social assistance"),
        _f("INDACCOMFOOD", "C24030", "026 053", "001",
           "Employed in accommodation and food services"),
    )),
    # HISPLFP divides by everyone 16+ (that is what participation means);
    # HISPUNEMPRATE divides by the labour force (that is what an unemployment
    # rate means). Dividing unemployment by total population would blend it with
    # retirement and school enrollment.
    TableSpec("C23002I", f"{HISP} 16 years and over", True, (
        _f("HISPLFP", "C23002I", "004 011 017 024", "001",
           "In the labor force (labor force participation rate)"),
        _f("HISPUNEMPRATE", "C23002I", "008 013 021 026", "004 011 017 024",
           "Unemployed as a share of the labor force",
           universe="Hispanic or Latino labor force 16 years and over"),
    )),
))

# ---------------------------------------------------------------------------
# H. Household Structure (Age, Marriage, Sex)
# ---------------------------------------------------------------------------
# Also home to the derived youth-dependency ratio (`DERIVED`, declared
# separately below because it is computed from other features, not fetched).
_H = Section("H", "Household Structure (Age, Marriage, Sex)", (
    TableSpec("B01002I", HISP, True, (
        _f("HISPMEDAGE", "B01002I", "001", "",
           "Median age of the Hispanic population"),
    )),
    # B01001I publishes 5-year bins by sex; collapsed to four bands (both sexes)
    # because 5-year bins are mostly noise at tract level.
    TableSpec("B01001I", HISP, True, (
        _f("HISPUNDER18", "B01001I", "003 004 005 006 018 019 020 021", "001",
           "Under 18 years"),
        _f("HISP18TO34", "B01001I", "007 008 009 010 022 023 024 025", "001",
           "18 to 34 years"),
        _f("HISP35TO64", "B01001I", "011 012 013 026 027 028", "001",
           "35 to 64 years"),
        _f("HISP65PLUS", "B01001I", "014 015 016 029 030 031", "001",
           "65 years and over"),
    )),
    TableSpec("B11001I", "Households with a Hispanic or Latino householder", True, (
        _f("HISPHHMARRIED", "B11001I", "003", "001",
           "Married-couple family households"),
        _f("HISPHHMALENOSPOUSE", "B11001I", "005", "001",
           "Male householder, no spouse present"),
        _f("HISPHHFEMALENOSPOUSE", "B11001I", "006", "001",
           "Female householder, no spouse present"),
        _f("HISPHHALONE", "B11001I", "008", "001", "Householder living alone"),
    )),
    TableSpec("B11001", "All households", False, (
        _f("HHMARRIEDALL", "B11001", "003", "001",
           "Married-couple family households, county-wide"),
    )),
))

# ---------------------------------------------------------------------------
# I. Racial and Ethnic Composition
# ---------------------------------------------------------------------------
_I = Section("I", "Racial and Ethnic Composition", (
    TableSpec("B03002", "Total population", False, (
        _f("NHWHITESHARE", "B03002", "003", "001", "Non-Hispanic White alone"),
        _f("NHBLACKSHARE", "B03002", "004", "001",
           "Non-Hispanic Black or African American alone"),
        _f("NHAIANSHARE", "B03002", "005", "001",
           "Non-Hispanic American Indian and Alaska Native alone"),
        _f("NHASIANSHARE", "B03002", "006", "001", "Non-Hispanic Asian alone"),
        _f("NHMULTISHARE", "B03002", "009", "001",
           "Non-Hispanic, two or more races -- the county's non-Hispanic "
           "propensity for multiracial reporting"),
        _f("HISPSHARE", "B03002", "012", "001", "Hispanic or Latino, any race"),
    )),
))

SECTIONS: tuple[Section, ...] = (_A, _B, _C, _D, _E, _F, _G, _H, _I)

# ---------------------------------------------------------------------------
# Derived features -- computed from the columns above, no extra API calls.
# ---------------------------------------------------------------------------
# Kept deliberately minimal: every entry here must be a plain arithmetic
# combination of published counts, not a constructed index. A diversity/entropy
# index over the origin and race shares was considered and removed -- it was the
# only quantity in the extract that measured something the Census does not
# publish, and the case for it was a hypothesis rather than a measurement.
#
# HISPYOUTHDEP belongs to group H (household).
DERIVED: tuple[tuple[str, str, str], ...] = (
    ("HISPYOUTHDEP", "B01001I",
     "Youth dependency ratio: HISPUNDER18 divided by (HISP18TO34 + HISP35TO64), "
     "i.e. Hispanic children per Hispanic working-age adult."),
)

# ---------------------------------------------------------------------------
# Diagnostic columns -- fetched, written to disk, NEVER modeled.
# ---------------------------------------------------------------------------
# These are the ACS's own measurement of the outcome variable. The outcome is
# built in the clean stage from the decennial PL tables; B03002_018E over
# B03002_012E is the same quantity from a different survey. A forest given that
# column splits on it almost exclusively and learns nothing else.
DIAGNOSTIC: tuple[tuple[str, str, str], ...] = (
    ("DIAG_ACSHISPSORALONE", "B03002_018E",
     "Hispanic, Some Other Race alone (ACS measurement of the outcome)"),
    ("DIAG_ACSHISPWHITEALONE", "B03002_013E",
     "Hispanic, White alone (ACS measurement of the outcome)"),
    ("DIAG_ACSHISPTWOORMORE", "B03002_019E",
     "Hispanic, two or more races (ACS measurement of the outcome)"),
)

DIAGNOSTIC_PREFIX = "DIAG_"

# ---------------------------------------------------------------------------
# Auxiliary columns -- fetched and renamed, never modeled, consumed by
# clean-stage derivations of OTHER sources' features.
# ---------------------------------------------------------------------------
AUXILIARY: tuple[tuple[str, str, str], ...] = (
    ("VOTINGAGEPOP", "B29001_001E",
     "Population 18 years and over -- the denominator of TURNOUT (two-party "
     "votes per voting-age resident), which is derived in the clean stage "
     "where the election columns and this ACS column meet"),
)

# ---------------------------------------------------------------------------
# Prior-vintage features: population change, 2011-2015 -> 2016-2020. Group D.
# ---------------------------------------------------------------------------
# Distinguishes established Hispanic communities from new destinations, a
# concept none of the point-in-time features capture.
#
# Stored as a LOG RATIO, log(H2020 + 1) - log(H2015 + 1), not a percent change.
# For a random forest the two are interchangeable -- they are monotone
# transforms of each other, so they produce identical trees -- but percent
# change is undefined in the 11 counties with no Hispanic residents in 2015 and
# reaches 3,738% at the top. The log ratio is defined everywhere and runs from
# about -1.9 to 1.7 across the middle 98% of counties. Positive means growth;
# 0.13 is the national median, roughly 14% growth.
#
# (feature name, census code compared across vintages, meaning)
GROWTH_FEATURES: tuple[tuple[str, str, str], ...] = (
    ("HISPGROWTH", "B03001_003E",
     "Change in the county Hispanic population from the 2011-2015 ACS to the "
     "2016-2020 ACS, as a log ratio: log(2020 + 1) - log(2015 + 1). Positive "
     "means growth."),
    # Measures something HISPGROWTH does not: Spearman between the two is only
    # +0.27. Three times as many counties are losing foreign-born residents
    # (1,332) as are losing Hispanic residents (418), because Hispanic growth is
    # increasingly US-born -- a county can gain Hispanics while losing immigrants.
    ("FBGROWTH", "B05002_013E",
     "Change in the county foreign-born population from the 2011-2015 ACS to "
     "the 2016-2020 ACS, as a log ratio. Positive means growth."),
)

PRIOR_CODES: tuple[str, ...] = tuple(code for _, code, _ in GROWTH_FEATURES)

# The prior-vintage fetch returns the SAME code names as the 2016-2020 fetch
# (both vintages publish B03001_003E, etc.), so its columns are suffixed at
# fetch time to keep the two vintages distinct in the merged dataset. The
# clean stage computes each growth feature from `code` vs `code + PRIOR_SUFFIX`.
PRIOR_SUFFIX = "_PRIOR"

# The Hispanic population count. Almost every feature in this spec is measured
# on a Hispanic universe, so this column is what governs whether any of them are
# measurable in a given unit -- it is the size variable the clean stage's
# coverage diagnostics are reported against.
HISPANIC_POPULATION_CODE = "B03001_003E"


# ---------------------------------------------------------------------------
# Accessors
# ---------------------------------------------------------------------------
def iter_features():
    """Yield every `Feature` across all sections, in declaration order."""
    for section in SECTIONS:
        for table in section.tables:
            yield from table.features


def estimate_codes() -> list[str]:
    """Every raw `..._###E` column the fetch needs, deduplicated and sorted.

    Includes numerators, denominators, and the diagnostic columns. Sorted so the
    request order is stable across runs (which keeps the on-disk column order
    stable, which keeps diffs readable).
    """
    codes: set[str] = set()
    for feature in iter_features():
        codes.update(feature.numerator_codes)
        codes.update(feature.denominator_codes)
    codes.update(code for _, code, _ in DIAGNOSTIC)
    codes.update(code for _, code, _ in AUXILIARY)
    return sorted(codes)


def moe_codes() -> list[str]:
    """The margin-of-error twin of every estimate column (`...E` -> `...M`).

    Medians carry MOEs too, so this is a blanket transform with no exceptions.
    """
    return [code[:-1] + "M" for code in estimate_codes()]


def all_codes(include_moe: bool = True) -> list[str]:
    """Full request list: estimates, optionally followed by their margins."""
    codes = estimate_codes()
    return codes + moe_codes() if include_moe else codes
