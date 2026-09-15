"""The dataset's feature manifest: every modeled feature, partitioned by theme.

Each ingest source declares its own features in its `_vars` file (`acs/acs_spec.py`,
`dhc/dhc_vars.py`, `geometry/geometry_vars.py`, `election/election_vars.py`);
this module aggregates those declarations and is
the ONLY place the thematic model groups are defined. The import arrow points
one way: the manifest imports from every source, and no source knows the
manifest exists.

`_check_partition()` runs at import and refuses to load a manifest that
disagrees with the sources: every feature in exactly one group, the ACS
sections mirroring their same-letter groups, and the groups exactly covering
what the sources declare.
"""

from __future__ import annotations

from build_dataset.ingest.acs.acs_spec import (
    AUXILIARY,
    DERIVED,
    DIAGNOSTIC,
    GROWTH_FEATURES,
    SECTIONS,
    iter_features,
)
from build_dataset.ingest.dhc.dhc_vars import DHC_FEATURES
from build_dataset.ingest.election.election_vars import ELECTION_FEATURES
from build_dataset.ingest.geometry.geometry_vars import GEOMETRY_FEATURES


def feature_names(level: str = "county") -> list[str]:
    """Names of every feature the census fetches produce: ACS, derived, and DHC.

    Does NOT include the geometry and election features, which other sources
    produce; `_check_partition` accounts for those separately.

    The growth features exist only at county level. Tract boundaries were
    redrawn between the 2011-2015 and 2016-2020 ACS vintages, so at tract
    level the two vintages describe DIFFERENT areas and the log ratio is not
    a growth measure — the extract refuses to compute it there, and excluding
    the names here means no model matrix can ever ask for it.
    """
    names = (
        [f.name for f in iter_features()]
        + [name for name, _, _ in DERIVED]
        + [name for name, _, _, _ in DHC_FEATURES]
    )
    if level == "county":
        names += [name for name, _, _ in GROWTH_FEATURES]
    return names


# ---------------------------------------------------------------------------
# Model feature groups (for group-isolation modeling)
# ---------------------------------------------------------------------------
# The authoritative partition of the model matrix into themes. The ACS spec's
# sections mirror these letters for the ACS features; the groups additionally
# place the derived, growth, DHC, geometry, and election features. The config
# layer filters each list to the features that exist at the requested
# level/elections setting and asserts the partition there.
#
# Assignment judgment calls, recorded so they are argued once:
#   - The six nativity x language cross-tabs sit under LANGUAGE: they measure
#     English ability, conditioned on nativity.
#   - FBLATAMSHARE is ORIGIN (where the foreign born are from), while the
#     entry-cohort shares are MOBILITY (when they came).
#   - PRBORNSHARE is MOBILITY: island-born Puerto Ricans are migrants the
#     foreign-born measures cannot see, though citizens by birth.
#   - HISPGROWTH / FBGROWTH are MOBILITY: population change as in-migration.
#   - The computer/broadband trio is INCOME: material-resource proxies.
#   - TURNOUT and NUMBEROFVOTERS sit under POLITICAL PREFERENCE though they
#     measure participation and size; only VOTELEAN is preference proper.
#
# {letter: (slug, title, feature names)}. Letters and slugs are stable CLI
# arguments and output-directory names.
MODEL_GROUPS: dict[str, tuple[str, str, tuple[str, ...]]] = {
    "A": ("language", "Language", (
        "HISPENGONLY", "HISPSPANVERYWELL", "HISPSPANWELL", "HISPSPANNOTWELL",
        "HISPSPANNOTATALL", "HISPOTHERLANG", "HISPNATIVEENGONLY",
        "HISPNATIVEOTHERVW", "HISPNATIVEOTHERLTVW", "HISPFBENGONLY",
        "HISPFBOTHERVW", "HISPFBOTHERLTVW",
    )),
    "B": ("citizenship", "US Citizenship and Residency Status", (
        "HISPADULTNATURALIZED", "HISPADULTNONCITIZEN",
    )),
    "C": ("origin", "National Origin and Background", (
        "MEXICANORIGIN", "PUERTORICANORIGIN", "CUBANORIGIN", "DOMINICANORIGIN",
        "CENTRALAMORIGIN", "GUATEMALANORIGIN", "HONDURANORIGIN",
        "SALVADORANORIGIN", "SOUTHAMORIGIN", "COLOMBIANORIGIN",
        "ECUADORIANORIGIN", "PERUVIANORIGIN", "VENEZUELANORIGIN",
        "OTHERORIGINTOTAL", "SPANIARDORIGIN", "HISPORIGINUNSPECIFIED",
        "FBLATAMSHARE",
    )),
    "D": ("mobility", "Mobility and Time in the U.S.", (
        "HISPADULTFB", "HISPCHILDFB", "FOREIGNBORNSHARE", "PRBORNSHARE",
        "FBENTERED2010PLUS", "FBENTERED2000S", "FBENTERED1990S",
        "FBENTEREDPRE1990", "LATAMFBENTERED2010PLUS", "LATAMFBENTERED2000S",
        "LATAMFBENTERED1990S", "LATAMFBENTEREDPRE1990",
        "HISPMOVEDWITHINCOUNTY", "HISPMOVEDDIFFCOUNTY", "HISPMOVEDDIFFSTATE",
        "HISPMOVEDABROAD", "HISPGROWTH", "FBGROWTH",
    )),
    "E": ("education", "Education", (
        "HISPEDULTHS", "HISPEDUHS", "HISPEDUSOMECOLL", "HISPEDUBAPLUS",
    )),
    "F": ("income", "Income and Affluence", (
        "HISPPERCAPINCOME", "HISPPOVERTY", "HISPSNAP", "HISPOWNEROCC",
        "HISPCROWDING", "HISPBROADBAND", "HISPCOMPUTERNOBROADBAND",
        "HISPNOCOMPUTER",
    )),
    "G": ("employment", "Employment and Industry", (
        "HISPOCCMGMT", "HISPOCCSERVICE", "HISPOCCSALESOFFICE",
        "HISPOCCNATRESCONST", "HISPOCCPRODTRANS", "INDAGRICULTURE",
        "INDCONSTRUCTION", "INDMANUFACTURING", "INDEDUHEALTH", "INDACCOMFOOD",
        "HISPLFP", "HISPUNEMPRATE",
    )),
    "H": ("household", "Household Structure (Age, Marriage, Sex)", (
        "HISPMEDAGE", "HISPUNDER18", "HISP18TO34", "HISP35TO64", "HISP65PLUS",
        "HISPYOUTHDEP", "HISPHHMARRIED", "HISPHHMALENOSPOUSE",
        "HISPHHFEMALENOSPOUSE", "HISPHHALONE", "HHMARRIEDALL",
    )),
    "I": ("racialcomp", "Racial and Ethnic Composition", (
        "NHWHITESHARE", "NHBLACKSHARE", "NHAIANSHARE", "NHASIANSHARE",
        "NHMULTISHARE", "HISPSHARE",
    )),
    "J": ("geography", "Geography and Urbanity", (
        "URBANSHARE", "DENSITY", "INTPTLON", "INTPTLAT",
    )),
    "K": ("elections", "Political Preference", (
        "VOTELEAN", "TURNOUT", "NUMBEROFVOTERS",
    )),
}

# Letter -> slug, e.g. so the CLI accepts `--group D` for `--group mobility`.
GROUP_SLUGS = {letter: slug for letter, (slug, _t, _f) in MODEL_GROUPS.items()}


def model_features(level: str = "county") -> list[str]:
    """Every feature a model matrix may contain at this level, in manifest order.

    The census-fetch features plus the geometry and election features -- the
    97 columns MODEL_GROUPS partitions (fewer at tract level, where the growth
    features do not exist).
    """
    return (
        feature_names(level)
        + [name for name, _ in GEOMETRY_FEATURES]
        + [name for name, _ in ELECTION_FEATURES]
    )


def group_features(groups: list[str], level: str = "county") -> list[str]:
    """Feature names for one or more model groups, by letter or slug.

    `group_features(["D"])` is one group; `group_features(["D", "J"])` is a
    two-group matrix. Unknown selectors raise. Features that do not exist at
    the requested level (the growth pair at tract level) are excluded, same
    as `model_features`.
    """
    by_slug = {slug: letter for letter, slug in GROUP_SLUGS.items()}
    names: list[str] = []
    for group in groups:
        letter = group if group in MODEL_GROUPS else by_slug.get(group)
        if letter is None:
            raise KeyError(
                f"unknown model group {group!r}; letters are "
                f"{list(MODEL_GROUPS)}, slugs are {sorted(by_slug)}"
            )
        names.extend(MODEL_GROUPS[letter][2])
    at_level = set(model_features(level))
    return [name for name in names if name in at_level]


def processed_columns(level: str = "county") -> list[str]:
    """The processed dataset's schema: every analysis-ready column, in order.

    Identifiers, the named PL counts, the targets and their derivations, the
    full model-feature layer, and the never-modeled diagnostics/auxiliaries.
    Raw census codes and MOEs stay in the raw artifact; anything listed here
    must exist in the cleaned frame (build asserts it).
    """
    ids = ["GEOID", "NAME"]
    pl_counts = [
        "TOTALPOP", "HISPANIC",
        "WHITEALONE", "SORALONE", "WHITESOR", "WHITEALONEORCOMBO",
        "NONHISPANICWHITEALONE", "NONHISPANICSORALONE", "NONHISPANICWHITESOR",
        "NONHISPANICWHITEALONEORCOMBO",
        "HSOR", "H_N_SOR", "HWHITE", "H_N_WHITE",
        "HWHITESOR", "H_N_WHITESOR", "HWHITEACOMBO", "H_N_WHITEACOMBO",
    ]
    targets = [
        "Hisp Pct of Pop",
        # descriptive shares: each Hispanic race choice over TOTALPOP
        "Hisp SOR Alone Pct of Pop", "Hisp White Alone Pct of Pop",
        "Hisp White SOR Pct of Pop", "Hisp White Pct of Pop",
        # regression targets: the same choices over HISPANIC
        "Hisp SOR Alone Pct of Hisp", "Hisp White Alone Pct of Hisp",
        "Hisp White SOR Pct of Hisp", "Hisp White Pct of Hisp",
        # classification targets
        "largest", "Most_SOR", "Most_White_SOR", "Most_White",
    ]
    extras = [name for name, _, _ in DIAGNOSTIC + AUXILIARY]
    return ids + pl_counts + targets + model_features(level) + extras


# ---------------------------------------------------------------------------
# Consistency: sources and groups must agree, and the groups must partition.
# ---------------------------------------------------------------------------
def _check_partition() -> None:
    grouped = [n for _slug, _title, names in MODEL_GROUPS.values() for n in names]
    dupes = sorted({n for n in grouped if grouped.count(n) > 1})
    assert not dupes, f"feature(s) in more than one model group: {dupes}"

    by_letter = {letter: set(names) for letter, (_s, _t, names) in MODEL_GROUPS.items()}
    for section in SECTIONS:
        assert section.title == MODEL_GROUPS[section.letter][1], (
            f"ACS section {section.letter} title differs from its model group"
        )
        stray = {
            f.name for table in section.tables for f in table.features
        } - by_letter[section.letter]
        assert not stray, (
            f"ACS section {section.letter} declares feature(s) outside group "
            f"{section.letter}: {sorted(stray)}"
        )

    expected = (
        set(feature_names("county"))
        | {name for name, _ in GEOMETRY_FEATURES}
        | {name for name, _ in ELECTION_FEATURES}
    )
    assert set(grouped) == expected, (
        "MODEL_GROUPS does not partition the model matrix: "
        f"missing {sorted(expected - set(grouped))}, "
        f"extra {sorted(set(grouped) - expected)}"
    )


_check_partition()
