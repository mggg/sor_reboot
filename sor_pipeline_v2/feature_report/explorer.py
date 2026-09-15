"""Build report/explorer.html: the self-contained interactive feature explorer.

Writes one `.html` file with no external dependencies: open it by
double-clicking, no Python and no server. It is a snapshot of one build, so
it lives beside that build's parquets and records what the features looked
like when they were built.

Auditing needs provenance as much as distribution, so each feature is shown
with its source census columns, its published universe, and its plain-English
meaning pulled from the spec -- alongside the histogram, the summary
statistics, and the counties at both extremes. The stats sit in two rows:
Distribution, then Data quality (the missingness causes and "could be
zero %" from feature_reliability.csv, each cell with a hover explanation).
Both share families appear under their denominator-stating names, and every
chart carries a title and a PNG-export button.

Deliberately hand-rolled rather than built on a plotting library: inlining one
would add several megabytes and still not give per-bar county names on hover.

Run: `python -m feature_report.explorer` (after `build_dataset.main` and
`feature_report.main` have written the parquets and the reliability table).
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from build_dataset import manifest
from build_dataset.clean import acs as clean_acs
from build_dataset.ingest.acs import acs_spec
from build_dataset.ingest.dhc import dhc_vars
from utils import config

# Counties named per histogram bar in the tooltip. Bars routinely hold hundreds
# of counties; the point is a sniff test, not an exhaustive list.
COUNTIES_PER_TOOLTIP = 8
# Rows in the high/low tables. The extremes are where a bad denominator or a
# misread universe shows up first.
EXTREME_ROWS = 12
# Values are rounded before embedding; 5 decimals is well past the precision of
# any ACS share and roughly halves the file.
VALUE_PRECISION = 5

# Full state name -> USPS abbreviation. The county NAME field spells the state
# out ("Autauga County, Alabama"), which is too long for a tooltip listing eight
# counties at once. Territories are included because the dataset spine carries
# them even though the ACS county universe does not.
STATE_ABBREV: dict[str, str] = {
    "Alabama": "AL",
    "Alaska": "AK",
    "Arizona": "AZ",
    "Arkansas": "AR",
    "California": "CA",
    "Colorado": "CO",
    "Connecticut": "CT",
    "Delaware": "DE",
    "District of Columbia": "DC",
    "Florida": "FL",
    "Georgia": "GA",
    "Hawaii": "HI",
    "Idaho": "ID",
    "Illinois": "IL",
    "Indiana": "IN",
    "Iowa": "IA",
    "Kansas": "KS",
    "Kentucky": "KY",
    "Louisiana": "LA",
    "Maine": "ME",
    "Maryland": "MD",
    "Massachusetts": "MA",
    "Michigan": "MI",
    "Minnesota": "MN",
    "Mississippi": "MS",
    "Missouri": "MO",
    "Montana": "MT",
    "Nebraska": "NE",
    "Nevada": "NV",
    "New Hampshire": "NH",
    "New Jersey": "NJ",
    "New Mexico": "NM",
    "New York": "NY",
    "North Carolina": "NC",
    "North Dakota": "ND",
    "Ohio": "OH",
    "Oklahoma": "OK",
    "Oregon": "OR",
    "Pennsylvania": "PA",
    "Rhode Island": "RI",
    "South Carolina": "SC",
    "South Dakota": "SD",
    "Tennessee": "TN",
    "Texas": "TX",
    "Utah": "UT",
    "Vermont": "VT",
    "Virginia": "VA",
    "Washington": "WA",
    "West Virginia": "WV",
    "Wisconsin": "WI",
    "Wyoming": "WY",
    "Puerto Rico": "PR",
    "American Samoa": "AS",
    "Guam": "GU",
    "Commonwealth of the Northern Mariana Islands": "MP",
    "United States Virgin Islands": "VI",
}

# State FIPS -> (full name, USPS abbreviation). Used in preference to parsing the
# NAME field, because NAME is not consistent across sources: the DHC fetch
# returns "Autauga County, Alabama" while the TIGER geometry in the joined
# dataset returns bare "Autauga". The GEOID prefix is always there.
STATE_FIPS_NAMES: dict[str, tuple[str, str]] = {
    "01": ("Alabama", "AL"),
    "02": ("Alaska", "AK"),
    "04": ("Arizona", "AZ"),
    "05": ("Arkansas", "AR"),
    "06": ("California", "CA"),
    "08": ("Colorado", "CO"),
    "09": ("Connecticut", "CT"),
    "10": ("Delaware", "DE"),
    "11": ("District of Columbia", "DC"),
    "12": ("Florida", "FL"),
    "13": ("Georgia", "GA"),
    "15": ("Hawaii", "HI"),
    "16": ("Idaho", "ID"),
    "17": ("Illinois", "IL"),
    "18": ("Indiana", "IN"),
    "19": ("Iowa", "IA"),
    "20": ("Kansas", "KS"),
    "21": ("Kentucky", "KY"),
    "22": ("Louisiana", "LA"),
    "23": ("Maine", "ME"),
    "24": ("Maryland", "MD"),
    "25": ("Massachusetts", "MA"),
    "26": ("Michigan", "MI"),
    "27": ("Minnesota", "MN"),
    "28": ("Mississippi", "MS"),
    "29": ("Missouri", "MO"),
    "30": ("Montana", "MT"),
    "31": ("Nebraska", "NE"),
    "32": ("Nevada", "NV"),
    "33": ("New Hampshire", "NH"),
    "34": ("New Jersey", "NJ"),
    "35": ("New Mexico", "NM"),
    "36": ("New York", "NY"),
    "37": ("North Carolina", "NC"),
    "38": ("North Dakota", "ND"),
    "39": ("Ohio", "OH"),
    "40": ("Oklahoma", "OK"),
    "41": ("Oregon", "OR"),
    "42": ("Pennsylvania", "PA"),
    "44": ("Rhode Island", "RI"),
    "45": ("South Carolina", "SC"),
    "46": ("South Dakota", "SD"),
    "47": ("Tennessee", "TN"),
    "48": ("Texas", "TX"),
    "49": ("Utah", "UT"),
    "50": ("Vermont", "VT"),
    "51": ("Virginia", "VA"),
    "53": ("Washington", "WA"),
    "54": ("West Virginia", "WV"),
    "55": ("Wisconsin", "WI"),
    "56": ("Wyoming", "WY"),
    "60": ("American Samoa", "AS"),
    "66": ("Guam", "GU"),
    "69": ("Northern Mariana Islands", "MP"),
    "72": ("Puerto Rico", "PR"),
    "78": ("U.S. Virgin Islands", "VI"),
}


def _provenance() -> dict[str, dict[str, str]]:
    """Source columns, universe, and meaning for every feature, from the spec.

    The displayed `section` is the feature's MODEL GROUP (manifest.MODEL_GROUPS),
    so the explorer's dropdown mirrors the group-isolation taxonomy. The
    provenance-oriented section it was declared under (extraction section,
    Derived, DHC, Cross-vintage change) is preserved as `source_section`.
    """
    out: dict[str, dict[str, str]] = {}
    for section in acs_spec.SECTIONS:
        for table in section.tables:
            for feature in table.features:
                out[feature.name] = {
                    "section": f"{section.letter}. {section.title}",
                    "table": table.table,
                    # The feature's own universe wins where it has one: those
                    # are the features whose denominator is a subtotal, so the
                    # table universe would overstate what the share is over.
                    "universe": (feature.universe or table.universe)
                    + ("" if table.hispanic_universe else "  (whole population)"),
                    "numerator": ", ".join(feature.numerator_codes),
                    "denominator": ", ".join(feature.denominator_codes) or "—",
                    "meaning": feature.meaning,
                }
    for name, source, meaning in acs_spec.DERIVED:
        out[name] = {
            "section": "Derived",
            "table": source,
            "universe": "computed from the columns above",
            "numerator": "—",
            "denominator": "—",
            "meaning": meaning,
        }
    for name, numerator, denominator, meaning in dhc_vars.DHC_FEATURES:
        out[name] = {
            "section": "Decennial (2020 DHC)",
            "table": "P2",
            "universe": "Total population (complete count, no margins of error)",
            "numerator": numerator,
            "denominator": denominator,
            "meaning": meaning,
        }
    for name, code, meaning in acs_spec.GROWTH_FEATURES:
        out[name] = {
            "section": "Cross-vintage change",
            "table": f"{code}, 2011-2015 vs 2016-2020 ACS",
            "universe": "log ratio: log(2020 + 1) - log(2015 + 1)",
            "numerator": f"{code} (2016-2020)",
            "denominator": f"{code} (2011-2015)",
            "meaning": meaning,
        }
    for letter, (_slug, title, names) in manifest.MODEL_GROUPS.items():
        for name in names:
            if name in out:
                out[name]["source_section"] = out[name]["section"]
                out[name]["section"] = f"{letter}. {title}"
    return out


def _share_label(meta: dict) -> str:
    """What the default view is actually showing, so the toggle is not a lie."""
    section = meta.get("source_section", meta.get("section", ""))
    if section == "Cross-vintage change":
        return "Log ratio"
    if meta.get("denominator", "\u2014") == "\u2014":
        return "Value"
    return "Share"


def _stats(values: pd.Series) -> dict:
    """Summary statistics for one feature, ignoring missing values."""
    clean = values.dropna()
    if clean.empty:
        return {"n": 0, "missing": int(values.isna().sum())}
    quantiles = clean.quantile([0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99])
    return {
        "n": int(clean.size),
        "missing": int(values.isna().sum()),
        "mean": float(clean.mean()),
        "sd": float(clean.std()),
        "min": float(clean.min()),
        "p1": float(quantiles[0.01]),
        "p5": float(quantiles[0.05]),
        "p25": float(quantiles[0.25]),
        "median": float(quantiles[0.5]),
        "p75": float(quantiles[0.75]),
        "p95": float(quantiles[0.95]),
        "p99": float(quantiles[0.99]),
        "max": float(clean.max()),
        "zeros": int((clean == 0).sum()),
    }


def _count_arrays(raw: pd.DataFrame) -> tuple[dict, dict, dict]:
    """Numerator and denominator COUNTS behind every share, for the raw view.

    Denominators are stored once in a shared table and referenced by key: the 81
    share features draw on only 22 distinct denominators, so storing them
    per-feature would trailer an extra megabyte of duplicated arrays onto the
    page for nothing.

    Returns (numerators_by_feature, denominators_by_key, denominator_key_by_feature).
    """
    clean = clean_acs.nullify_sentinels(raw)

    def summed(codes) -> list:
        values = clean[list(codes)].sum(axis=1, skipna=False)
        return [None if pd.isna(v) else int(v) for v in values]

    numerators: dict[str, list] = {}
    denominators: dict[str, list] = {}
    denominator_key: dict[str, str] = {}
    for feature in acs_spec.iter_features():
        numerators[feature.name] = summed(feature.numerator_codes)
        if feature.is_share:
            key = "+".join(feature.denominator_codes)
            denominator_key[feature.name] = key
            if key not in denominators:
                denominators[key] = summed(feature.denominator_codes)
    for _name, numerator, denominator, _meaning in dhc_vars.DHC_FEATURES:
        if numerator in clean.columns and denominator in clean.columns:
            numerators[_name] = summed((numerator,))
            denominator_key[_name] = denominator
            denominators.setdefault(denominator, summed((denominator,)))
    return numerators, denominators, denominator_key


def build_payload(
    features: pd.DataFrame,
    quality: pd.DataFrame | None = None,
    names: pd.Series | None = None,
    raw: pd.DataFrame | None = None,
    dhc_counts: pd.DataFrame | None = None,
) -> dict:
    """Assemble everything the page needs as one JSON-serializable dict."""
    modeled = set(manifest.feature_names("county"))
    columns = [
        c
        for c in features.columns
        if c not in ("GEOID", "NAME")
        and not c.startswith(acs_spec.DIAGNOSTIC_PREFIX)
        # Beyond the ACS features, take only the columns EXTRA_PROVENANCE can
        # describe. The joined dataset also carries ~65 raw P1_/P2_/B.. code
        # columns; listing those unexplained would bury the real variables.
        and (c in modeled or c in EXTRA_PROVENANCE)
    ]
    geoids = features["GEOID"].astype(str).tolist()
    if names is None:
        names = features["NAME"] if "NAME" in features else pd.Series(geoids)

    # County name, then state from the GEOID prefix. NAME is inconsistent across
    # sources -- "Autauga County, Alabama" from the DHC fetch, bare "Autauga"
    # from the TIGER geometry in the joined dataset -- but the first two digits
    # of GEOID are always the state.
    def split_name(value: object, geoid: str) -> tuple[str, str, str]:
        county = (
            str(value).rsplit(",", 1)[0].strip() if isinstance(value, str) else geoid
        )
        full, abbrev = STATE_FIPS_NAMES.get(str(geoid)[:2], ("Unknown", "??"))
        if full == "Unknown" and isinstance(value, str) and "," in value:
            # Fall back to the spelled-out state in NAME for any FIPS not listed.
            spelled = value.rsplit(",", 1)[-1].strip()
            full, abbrev = spelled, STATE_ABBREV.get(spelled, spelled)
        return county or geoid, full, abbrev

    parts = [split_name(name, geoid) for name, geoid in zip(names, geoids)]
    labels = [f"{county}, {abbrev}" for county, _full, abbrev in parts]

    imprecise = {}
    if quality is not None and "pct_imprecise" in quality.columns:
        imprecise = dict(zip(quality["feature"], quality["pct_imprecise"]))

    provenance = _provenance()
    for name, (section, source, universe, meaning) in EXTRA_PROVENANCE.items():
        provenance.setdefault(
            name,
            {
                "section": section,
                "table": source,
                "universe": universe,
                "numerator": source,
                "denominator": "—",
                "meaning": meaning,
            },
        )
    # The dropdown lists states spelled out; the tooltip abbreviates them.
    states = [full for _county, full, _abbrev in parts]
    counts_source = raw
    if raw is not None and dhc_counts is not None:
        counts_source = raw.merge(dhc_counts, on="GEOID", how="left")
    numerators, denominators, denominator_key = (
        _count_arrays(counts_source) if counts_source is not None else ({}, {}, {})
    )

    payload = {
        "counties": labels,
        "geoids": geoids,
        "states": states,
        "denominators": denominators,
        # Dropdown section order: model groups A-K first, context after,
        # outcomes fenced at the bottom. Unlisted sections sort alphabetically
        # at the end.
        "section_order": [
            f"{letter}. {title}"
            for letter, (_slug, title, _names) in manifest.MODEL_GROUPS.items()
        ]
        + [_POP, _BUILDING, _OUTCOME],
        "features": {},
    }
    for column in columns:
        series = features[column]
        rounded = series.round(VALUE_PRECISION)
        meta = provenance.get(column, {})
        # A feature only offers the count views when real count columns stand
        # behind it. Medians, the youth-dependency ratio and the growth log
        # ratios have no numerator to show, so their toggle is hidden rather
        # than showing something misleading.
        views = [{"id": "share", "label": _share_label(meta)}]
        # Counts are offered only for genuine shares. A median's "numerator" is
        # the median itself, so a count view there would just repeat the same
        # number under a label that says it is something else.
        if column in denominator_key:
            views.append({"id": "num", "label": "Numerator count"})
            views.append({"id": "den", "label": "Denominator count"})

        payload["features"][column] = {
            "values": [None if pd.isna(v) else float(v) for v in rounded],
            "num": numerators.get(column),
            "den": denominator_key.get(column),
            "views": views,
            "pct_imprecise": float(imprecise.get(column, 0.0)),
            "meta": provenance.get(
                column,
                {
                    "section": "—",
                    "table": "—",
                    "universe": "—",
                    "numerator": "—",
                    "denominator": "—",
                    "meaning": "—",
                },
            ),
        }
    return payload


_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Feature Explorer &mdash; __TITLE__</title>
<style>
  :root {
    --bg: #ffffff; --panel: #f6f6f4; --line: #d8d8d2; --ink: #1b1b19;
    --muted: #6b6b64; --accent: #2f6f5e; --accent-soft: #d7e6e0; --warn: #a2542a;
  }
  @media (prefers-color-scheme: dark) {
    :root:not([data-theme="light"]) {
      --bg: #16171a; --panel: #1e2024; --line: #33363c; --ink: #e9e9e6;
      --muted: #9a9a92; --accent: #6fb9a2; --accent-soft: #24413a; --warn: #d99263;
    }
  }
  :root[data-theme="dark"] {
    --bg: #16171a; --panel: #1e2024; --line: #33363c; --ink: #e9e9e6;
    --muted: #9a9a92; --accent: #6fb9a2; --accent-soft: #24413a; --warn: #d99263;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; background: var(--bg); color: var(--ink);
    font: 15px/1.55 ui-sans-serif, -apple-system, "Segoe UI", Roboto, sans-serif;
  }
  .wrap { max-width: 1100px; margin: 0 auto; padding: 28px 22px 64px; }
  h1 { font-size: 20px; margin: 0 0 4px; letter-spacing: -0.01em; }
  .sub { color: var(--muted); font-size: 13px; margin-bottom: 22px; }
  .picker { display: flex; gap: 12px; align-items: center; flex-wrap: wrap;
            padding: 14px; background: var(--panel); border: 1px solid var(--line);
            border-radius: 8px; margin-bottom: 20px; }
  select, input {
    font: inherit; padding: 7px 10px; border: 1px solid var(--line);
    border-radius: 6px; background: var(--bg); color: var(--ink); min-width: 260px;
  }
  label { font-size: 13px; color: var(--muted); }
  .meta { background: var(--panel); border: 1px solid var(--line); border-radius: 8px;
          padding: 14px 16px; margin-bottom: 20px; }
  .meta dl { display: grid; grid-template-columns: 150px 1fr; gap: 4px 14px; margin: 0; }
  .meta dt { color: var(--muted); font-size: 13px; }
  .meta dd { margin: 0; font-size: 13px; }
  code { font: 12.5px/1.4 ui-monospace, SFMono-Regular, Menlo, monospace;
         background: var(--accent-soft); padding: 1px 5px; border-radius: 4px; }
  .statlbl { font-size: 11px; text-transform: uppercase; letter-spacing: .05em;
             color: var(--muted); margin: 10px 0 4px; }
  .statgrid { display: grid; grid-template-columns: repeat(auto-fit, minmax(96px, 1fr));
              gap: 1px; background: var(--line); border: 1px solid var(--line);
              border-radius: 8px; overflow: hidden; margin-bottom: 22px; }
  .stat { background: var(--bg); padding: 9px 11px; }
  .stat .k { font-size: 11px; text-transform: uppercase; letter-spacing: .05em;
             color: var(--muted); }
  .stat .v { font-size: 15px; font-variant-numeric: tabular-nums; margin-top: 2px; }
  .chartbox { position: relative; border: 1px solid var(--line); border-radius: 8px;
              padding: 14px; background: var(--bg); margin-bottom: 22px; }
  svg { display: block; width: 100%; height: 340px; }
  .bar { fill: var(--accent); }
  .bar:hover { fill: var(--warn); }
  .axis { stroke: var(--line); }
  .tick { fill: var(--muted); font-size: 11px; font-variant-numeric: tabular-nums; }
  .axlabel { fill: var(--ink); font-size: 12px; font-weight: 600; }
  #tip { position: absolute; pointer-events: none; opacity: 0; transition: opacity .08s;
         background: var(--ink); color: var(--bg); padding: 9px 11px; border-radius: 6px;
         font-size: 12.5px; line-height: 1.5; max-width: 320px; z-index: 5; }
  #tip b { font-variant-numeric: tabular-nums; }
  .tables { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }
  @media (max-width: 720px) { .tables { grid-template-columns: 1fr; } }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  caption { text-align: left; font-size: 12px; text-transform: uppercase;
            letter-spacing: .05em; color: var(--muted); padding-bottom: 6px; }
  th, td { text-align: left; padding: 5px 8px; border-bottom: 1px solid var(--line); }
  td:last-child, th:last-child { text-align: right; font-variant-numeric: tabular-nums; }
  .note { font-size: 12.5px; color: var(--muted); margin-top: 26px;
          border-top: 1px solid var(--line); padding-top: 14px; }
</style>
</head>
<body>
<div class="wrap">
  <h1>Feature Explorer</h1>
  <div class="sub">__SUBTITLE__</div>

  <div class="picker">
    <label for="feat">Feature</label>
    <select id="feat"></select>
    <label for="state">State</label>
    <select id="state"></select>
    <label for="view">View</label>
    <select id="view"></select>
    <label for="yscale">Y scale</label>
    <select id="yscale" style="min-width:110px">
      <option value="log" selected>Log</option>
      <option value="linear">Linear</option>
    </select>
    <label for="xrange">X range</label>
    <select id="xrange" style="min-width:150px">
      <option value="99" selected>1st&ndash;99th pct</option>
      <option value="95">5th&ndash;95th pct</option>
      <option value="full">Full range</option>
    </select>
    <label for="bins">Bins</label>
    <input id="bins" type="number" value="40" min="5" max="120" style="min-width:80px">
  </div>

  <div class="meta">
    <dl>
      <dt>Meaning</dt><dd id="m-meaning"></dd>
      <dt>Section</dt><dd id="m-section"></dd>
      <dt>Source table</dt><dd id="m-table"></dd>
      <dt>Universe</dt><dd id="m-universe"></dd>
      <dt>Numerator</dt><dd id="m-num"></dd>
      <dt>Denominator</dt><dd id="m-den"></dd>
      <dt>Showing</dt><dd id="m-showing"></dd>
    </dl>
  </div>

  <div id="stats"></div>

  <div class="chartbox">
    <div id="clipnote" style="font-size:12.5px;color:var(--muted);margin-bottom:6px"></div>
    <div id="charttitle" style="font-weight:600;font-size:14.5px;margin:2px 0 6px"></div>
    <svg id="chart"></svg>
    <div style="text-align:right;margin-top:6px"><button id="exportbtn" style="font:12.5px inherit;padding:4px 12px;cursor:pointer;border:1px solid #bbb;border-radius:6px;background:#fff">Download chart (PNG)</button></div>
    <div id="tip"></div>
  </div>

  <div class="tables">
    <table id="lowtab"><caption>Lowest values</caption></table>
    <table id="hightab"><caption>Highest values</caption></table>
  </div>

  <p class="note">
    Hover a bar to see how many counties fall in that range and which ones.
    Extremes are where a wrong denominator or a misread universe shows up first,
    so the tables above are the fastest audit: if the top of a share is above 1,
    or the bottom of a count is negative, the feature is wrong.
    The <b>View</b> toggle switches between the derived share and the raw census
    counts it was built from &mdash; the numerator and the denominator separately &mdash;
    so a suspicious share can be traced straight back to the two numbers behind it.
    Features with no counts behind them (medians, the growth log ratios) offer no toggle.
    <b>Could be zero %</b> is the share of counties where the count could plausibly be
    <b>zero</b>. The ACS is a survey, not a headcount: a reported figure of 34 people
    with a margin of error of 40 means the true number is somewhere between 0 and 74,
    so the survey cannot rule out that there is nobody there. A feature at 25%
    is one where a quarter of counties are in that position. Counts of exactly zero are
    not flagged &mdash; the ACS attaches a fixed minimum margin to every zero, so they
    would all trip the test. Such values are reported but never removed: deleting
    one cell would drop that county from the model entirely, losing its other 84 features
    to fix one. Formally the test is <code>estimate &minus; MOE &lt; 0</code>, with margins
    combined in quadrature across any summed lines.
    This page is a snapshot of one extract run and does not update on its own.
  </p>
</div>
<script id="payload" type="application/json">__PAYLOAD__</script>
<script>
const DATA = JSON.parse(document.getElementById("payload").textContent);
const RELIABILITY = __RELIABILITY__;
const NAMES = DATA.counties;      // "Autauga County, AL" -- used in tooltips
const GEOIDS = DATA.geoids || [];  // kept out of tooltips, shown in the tables
const STATES = DATA.states;
const sel = document.getElementById("feat");
const stateSel = document.getElementById("state");
const viewSel = document.getElementById("view");
const binsInput = document.getElementById("bins");
const yScaleSel = document.getElementById("yscale");
const xRangeSel = document.getElementById("xrange");
const tip = document.getElementById("tip");

// Index sets are computed once per state so switching features is instant.
const ALL_IDX = NAMES.map((_, i) => i);
const stateNames = Array.from(new Set(STATES)).sort();
[["", "All states (" + ALL_IDX.length.toLocaleString() + " counties)"]]
  .concat(stateNames.map(s => [s, s]))
  .forEach(([v, label]) => {
    const o = document.createElement("option");
    o.value = v; o.textContent = label; stateSel.appendChild(o);
  });

function activeIndices() {
  const want = stateSel.value;
  return want ? ALL_IDX.filter(i => STATES[i] === want) : ALL_IDX;
}

// Computed in the browser, not precomputed in Python, so every figure reflects
// whatever subset the state filter has selected.
function computeStats(vals) {
  const clean = vals.filter(v => v !== null).sort((a, b) => a - b);
  const n = clean.length;
  if (!n) return {n: 0, missing: vals.length};
  const q = p => {
    const pos = (n - 1) * p, lo = Math.floor(pos), hi = Math.ceil(pos);
    return clean[lo] + (clean[hi] - clean[lo]) * (pos - lo);
  };
  const mean = clean.reduce((a, b) => a + b, 0) / n;
  const sd = n > 1
    ? Math.sqrt(clean.reduce((a, b) => a + (b - mean) ** 2, 0) / (n - 1))
    : 0;
  return {
    n, missing: vals.length - n, zeros: clean.filter(v => v === 0).length,
    mean, sd, min: clean[0], max: clean[n - 1],
    p1: q(0.01), p5: q(0.05), p25: q(0.25), median: q(0.5),
    p75: q(0.75), p95: q(0.95), p99: q(0.99),
  };
}

// Grouped so the outcome variables are visibly fenced off from the predictors
// rather than sitting alphabetically among them.
const bySection = {};
Object.keys(DATA.features).sort().forEach(k => {
  const sec = DATA.features[k].meta.section || "Other";
  (bySection[sec] = bySection[sec] || []).push(k);
});
const secOrder = DATA.section_order || [];
const secRank = s => { const i = secOrder.indexOf(s); return i < 0 ? secOrder.length : i; };
Object.keys(bySection).sort((a, b) => secRank(a) - secRank(b) || a.localeCompare(b)).forEach(sec => {
  const g = document.createElement("optgroup");
  g.label = sec;
  bySection[sec].forEach(k => {
    const o = document.createElement("option");
    o.value = k; o.textContent = k; g.appendChild(o);
  });
  sel.appendChild(g);
});

const fmt = v => {
  if (v === null || v === undefined || Number.isNaN(v)) return "\\u2014";
  const a = Math.abs(v);
  if (a !== 0 && (a < 0.001 || a >= 100000)) return v.toExponential(2);
  return (Math.round(v * 10000) / 10000).toLocaleString(undefined, {maximumFractionDigits: 4});
};

// Rebuilt per feature: not every feature has counts behind it, so the options
// depend on what the payload actually carries.
function syncViews(f) {
  const wanted = viewSel.value;
  viewSel.innerHTML = "";
  f.views.forEach(v => {
    const o = document.createElement("option");
    o.value = v.id; o.textContent = v.label; viewSel.appendChild(o);
  });
  const available = f.views.map(v => v.id);
  viewSel.value = available.includes(wanted) ? wanted : available[0];
  viewSel.disabled = available.length === 1;
}

// The array actually being displayed, and a human label for it.
function activeSeries(f) {
  if (viewSel.value === "num" && f.num) {
    return {vals: f.num, label: "raw count: " + f.meta.numerator, integer: true};
  }
  if (viewSel.value === "den" && f.den && DATA.denominators[f.den]) {
    return {vals: DATA.denominators[f.den], label: "raw count: " + f.meta.denominator,
            integer: true};
  }
  const share = f.views.find(v => v.id === "share");
  return {vals: f.values, label: (share ? share.label : "Share") + " (derived)",
          integer: false};
}

function renderMeta(f) {
  const m = f.meta;
  document.getElementById("m-meaning").textContent = m.meaning;
  document.getElementById("m-section").textContent = m.section;
  document.getElementById("m-table").innerHTML = "<code>" + m.table + "</code>";
  document.getElementById("m-universe").textContent = m.universe;
  document.getElementById("m-num").innerHTML = "<code>" + m.numerator + "</code>";
  document.getElementById("m-den").innerHTML = "<code>" + m.denominator + "</code>";
  document.getElementById("m-showing").textContent = activeSeries(f).label;
  const box = document.querySelector(".meta");
  const isOutcome = (m.section || "").startsWith("OUTCOME");
  box.style.borderColor = isOutcome ? "var(--warn)" : "var(--line)";
  box.style.borderWidth = isOutcome ? "2px" : "1px";
}

function renderStats(f, s) {
  const cell = (k, v, tip) =>
    `<div class="stat"${tip ? ` title="${tip}"` : ""}><div class="k">${k}</div><div class="v">${v}</div></div>`;
  const dist = [
    ["n", (s.n ?? 0).toLocaleString()], ["zeros", (s.zeros ?? 0).toLocaleString()],
    ["mean", fmtVal(s.mean)], ["sd", fmtVal(s.sd)],
    ["min", fmtVal(s.min)], ["p1", fmtVal(s.p1)], ["p5", fmtVal(s.p5)],
    ["p25", fmtVal(s.p25)], ["median", fmtVal(s.median)], ["p75", fmtVal(s.p75)],
    ["p95", fmtVal(s.p95)], ["p99", fmtVal(s.p99)], ["max", fmtVal(s.max)],
  ];
  const r = RELIABILITY[sel.value];
  let qual = cell("missing", (s.missing ?? 0).toLocaleString(),
    "Counties where this feature could not be computed at all");
  if (r) {
    qual +=
      cell("census declined", r.declined.toLocaleString(),
        "Of the missing: the Census printed a cannot-compute code instead of a value") +
      cell("nobody to measure", r.empty.toLocaleString(),
        "Of the missing: the feature's universe is empty there, so the share is a question about nobody (0/0)") +
      cell("never published", r.unpublished.toLocaleString(),
        "Of the missing: no value was published at all; whole tables for Puerto Rico, scattered cells elsewhere") +
      cell("could be zero %", fmt(r.could_be_zero_pct),
        "Value present but its 90% interval reaches zero: a figure of 34 people with a margin of 40 cannot rule out nobody. Reported, never removed.");
  } else {
    qual += cell("could be zero %", "&mdash;",
      "Not applicable: complete count or administrative source, no survey margin");
  }
  document.getElementById("stats").innerHTML =
    `<div class="statlbl">Distribution</div><div class="statgrid">${dist.map(([k, v]) => cell(k, v)).join("")}</div>` +
    `<div class="statlbl">Data quality (hover any cell for what it means)</div><div class="statgrid">${qual}</div>`;
}

let INTEGER_VIEW = false;
const fmtVal = v => (INTEGER_VIEW && v !== null && v !== undefined && !Number.isNaN(v))
  ? Math.round(v).toLocaleString() : fmt(v);

function renderTables(values) {
  const rows = values.map((v, i) => [v, i]).filter(r => r[0] !== null);
  rows.sort((a, b) => a[0] - b[0]);
  const draw = (id, subset, title) => {
    document.getElementById(id).innerHTML =
      `<caption>${title}</caption><tr><th>County</th><th>Value</th></tr>` +
      subset.map(([v, i]) =>
        `<tr><td>${NAMES[i]}${GEOIDS[i] ? ` <span style="color:var(--muted)">${GEOIDS[i]}</span>` : ""}` +
        `</td><td>${fmtVal(v)}</td></tr>`).join("");
  };
  draw("lowtab", rows.slice(0, __EXTREMES__), "Lowest values");
  draw("hightab", rows.slice(-__EXTREMES__).reverse(), "Highest values");
}

function renderChart(values, xLabel) {
  const svg = document.getElementById("chart");
  const clean = values.map((v, i) => [v, i]).filter(r => r[0] !== null);
  svg.innerHTML = "";
  if (!clean.length) return;

  const nBins = Math.max(5, Math.min(120, parseInt(binsInput.value) || 40));

  // These features are heavily zero-inflated and long-tailed: a single county
  // (Los Angeles on any count) stretches the axis so far that 98% of counties
  // land in the first bin. Trimming to a percentile range by default keeps the
  // body of the distribution legible; nothing is lost, because the outliers are
  // named in the extremes tables below.
  const sorted = clean.map(r => r[0]).sort((a, b) => a - b);
  const pick = p => {
    const pos = (sorted.length - 1) * p, l = Math.floor(pos), h = Math.ceil(pos);
    return sorted[l] + (sorted[h] - sorted[l]) * (pos - l);
  };
  const mode = xRangeSel.value;
  let lo = sorted[0], hi = sorted[sorted.length - 1];
  if (mode === "99") { lo = pick(0.01); hi = pick(0.99); }
  else if (mode === "95") { lo = pick(0.05); hi = pick(0.95); }
  if (!(hi > lo)) { lo = sorted[0]; hi = sorted[sorted.length - 1]; }

  const below = clean.filter(r => r[0] < lo).length;
  const above = clean.filter(r => r[0] > hi).length;
  const note = document.getElementById("clipnote");
  const label = xRangeSel.options[xRangeSel.selectedIndex].text;
  note.innerHTML = (below || above)
    ? `<b>X range = ${label}.</b> Bars cover ${fmtVal(lo)} to ${fmtVal(hi)}. `
      + `${below.toLocaleString()} ${below === 1 ? "county falls" : "counties fall"} below `
      + `and ${above.toLocaleString()} above that, so they are not drawn &mdash; but they are `
      + `still counted in every statistic above and named in the tables below. `
      + `Choose <i>Full range</i> to draw them.`
    : "";

  const span = (hi - lo) || 1;
  const bins = Array.from({length: nBins}, () => []);
  clean.forEach(([v, i]) => {
    if (v < lo || v > hi) return;
    let b = Math.floor(((v - lo) / span) * nBins);
    if (b >= nBins) b = nBins - 1;
    if (b < 0) b = 0;
    bins[b].push(i);
  });

  const W = svg.clientWidth || 900, H = 340;
  // Left and bottom padding leave room for the rotated y-axis title and the
  // x-axis title beneath the tick labels.
  const padL = 74, padR = 12, padT = 14, padB = 56;
  const plotW = W - padL - padR, plotH = H - padT - padB;
  const maxCount = Math.max(...bins.map(b => b.length)) || 1;
  // On a linear axis a bar holding 3 counties next to one holding 2,900 is a
  // fraction of a pixel. Log height is what makes the tail visible at all.
  const useLog = yScaleSel.value === "log";
  const ticksToDraw = [];
  const height = c => c <= 0 ? 0
    : (useLog ? Math.log10(1 + c) / Math.log10(1 + maxCount) : c / maxCount);
  const ns = "http://www.w3.org/2000/svg";
  const el = (tag, attrs) => {
    const e = document.createElementNS(ns, tag);
    for (const k in attrs) e.setAttribute(k, attrs[k]);
    return e;
  };

  // Gridlines are drawn at round COUNT values and positioned through the same
  // height() transform, so they stay correct under either scale.
  //
  // On a log axis the decade below the maximum can land within a pixel or two
  // of the maximum itself (max 1,200 puts the "1000" label on top of the
  // "1200" one), so candidates are placed largest-first and any that falls too
  // close to one already placed is dropped. The maximum always wins.
  const MIN_TICK_GAP = 15;
  const candidates = useLog
    ? [maxCount, ...[10000, 1000, 100, 10, 1].filter(v => v < maxCount)]
    : [maxCount, maxCount * 0.5, 0];
  const placed = [];
  candidates.forEach(count => {
    const y = padT + plotH - height(count) * plotH;
    if (placed.every(p => Math.abs(p - y) >= MIN_TICK_GAP)) {
      placed.push(y);
      ticksToDraw.push(count);
    }
  });
  ticksToDraw.forEach(count => {
    const y = padT + plotH - height(count) * plotH;
    svg.appendChild(el("line", {x1: padL, x2: W - padR, y1: y, y2: y, class: "axis"}));
    const t = el("text", {x: padL - 8, y: y + 4, class: "tick", "text-anchor": "end"});
    t.textContent = Math.round(count).toLocaleString();
    svg.appendChild(t);
  });

  const bw = plotW / nBins;
  bins.forEach((idxs, b) => {
    const h = height(idxs.length) * plotH;
    const rect = el("rect", {
      x: padL + b * bw + 0.5, y: padT + plotH - h,
      width: Math.max(bw - 1, 0.5), height: h, class: "bar",
    });
    const binLo = lo + (b / nBins) * span, binHi = lo + ((b + 1) / nBins) * span;
    rect.addEventListener("mousemove", ev => {
      const sample = idxs.slice(0, __TOOLTIP__).map(i => NAMES[i]);
      const more = idxs.length - sample.length;
      tip.innerHTML =
        `<b>${fmtVal(binLo)} &ndash; ${fmtVal(binHi)}</b><br>` +
        `<b>${idxs.length.toLocaleString()}</b> ${idxs.length === 1 ? "county" : "counties"}` +
        (sample.length ? "<br>" + sample.join("<br>") : "") +
        (more > 0 ? `<br><i>and ${more.toLocaleString()} more</i>` : "");
      const box = svg.parentElement.getBoundingClientRect();
      let x = ev.clientX - box.left + 14;
      if (x + 320 > box.width) x = ev.clientX - box.left - 334;
      tip.style.left = x + "px";
      tip.style.top = (ev.clientY - box.top + 14) + "px";
      tip.style.opacity = 1;
    });
    rect.addEventListener("mouseleave", () => { tip.style.opacity = 0; });
    svg.appendChild(rect);
  });

  [0, 0.25, 0.5, 0.75, 1].forEach(frac => {
    const t = el("text", {
      x: padL + frac * plotW, y: H - 26,
      class: "tick", "text-anchor": frac === 0 ? "start" : frac === 1 ? "end" : "middle",
    });
    t.textContent = fmtVal(lo + frac * span);
    svg.appendChild(t);
  });

  const xTitle = el("text", {
    x: padL + plotW / 2, y: H - 6, class: "axlabel", "text-anchor": "middle",
  });
  xTitle.textContent = xLabel;
  svg.appendChild(xTitle);

  const yTitle = el("text", {
    x: 14, y: padT + plotH / 2, class: "axlabel", "text-anchor": "middle",
    transform: `rotate(-90 14 ${padT + plotH / 2})`,
  });
  yTitle.textContent = "Number of counties" + (useLog ? " (log scale)" : "");
  svg.appendChild(yTitle);
}

function render() {
  const f = DATA.features[sel.value];
  syncViews(f);
  const series = activeSeries(f);
  INTEGER_VIEW = series.integer;
  const idx = activeIndices();
  // Set membership, not Array.includes -- the latter is O(n) per lookup and
  // turns this into 10M comparisons on a 3,221-county national extract.
  const keep = new Set(idx);
  // Values are blanked rather than compacted so the original row positions
  // survive; tooltips and tables index straight back into NAMES.
  const vals = NAMES.map((_, i) => keep.has(i) ? series.vals[i] : null);
  renderMeta(f);
  renderStats(f, computeStats(idx.map(i => series.vals[i])));
  document.getElementById("charttitle").textContent = "Distribution of " + sel.value + " across U.S. counties";
  renderChart(vals, sel.value + " \u2014 " + series.label);
  renderTables(vals);
}

sel.addEventListener("change", render);
stateSel.addEventListener("change", render);
viewSel.addEventListener("change", render);
binsInput.addEventListener("input", render);
yScaleSel.addEventListener("change", render);
xRangeSel.addEventListener("change", render);
window.addEventListener("resize", render);
document.getElementById("exportbtn").addEventListener("click", () => {
  const svg = document.getElementById("chart");
  const clone = svg.cloneNode(true);
  const cs = getComputedStyle(document.documentElement);
  const v = name => cs.getPropertyValue(name).trim();
  const st = document.createElementNS("http://www.w3.org/2000/svg", "style");
  st.textContent =
    `.bar{fill:${v("--accent") || "#2563eb"};}` +
    `.axis{stroke:${v("--line") || "#ddd"};}` +
    `text{font:12px -apple-system,Arial,sans-serif;fill:#444;}` +
    `.axlabel{font-size:12.5px;fill:#111;}`;
  clone.insertBefore(st, clone.firstChild);
  const W = svg.clientWidth || 900, H = 340, TITLE = 30;
  clone.setAttribute("xmlns", "http://www.w3.org/2000/svg");
  clone.setAttribute("width", W);
  clone.setAttribute("height", H);
  const img = new Image();
  img.onload = () => {
    const canvas = document.createElement("canvas");
    const s = 2;
    canvas.width = W * s; canvas.height = (H + TITLE) * s;
    const ctx = canvas.getContext("2d");
    ctx.scale(s, s);
    ctx.fillStyle = "#ffffff"; ctx.fillRect(0, 0, W, H + TITLE);
    ctx.fillStyle = "#111"; ctx.font = "600 15px -apple-system, Arial, sans-serif";
    ctx.fillText(document.getElementById("charttitle").textContent, 12, 20);
    ctx.drawImage(img, 0, TITLE, W, H);
    canvas.toBlob(b => {
      const a = document.createElement("a");
      a.href = URL.createObjectURL(b);
      a.download = sel.value + "_distribution.png";
      a.click();
      URL.revokeObjectURL(a.href);
    }, "image/png");
  };
  img.src = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(new XMLSerializer().serializeToString(clone));
});
render();
</script>
</body>
</html>
"""


def write_explorer(
    features: pd.DataFrame,
    path: Path,
    quality: pd.DataFrame | None = None,
    subtitle: str = "",
    raw: pd.DataFrame | None = None,
    dhc_counts: pd.DataFrame | None = None,
    reliability: dict | None = None,
) -> Path:
    """Write the self-contained HTML explorer and return its path.

    Passing `raw` enables the raw-count views; without it the page shows shares
    only. `reliability` maps ACS feature name -> the Data-quality cells
    (declined / empty / unpublished / could_be_zero_pct); features absent from
    it show an em dash with a no-survey-margin tooltip.
    """
    payload = build_payload(features, quality=quality, raw=raw, dhc_counts=dhc_counts)
    html = (
        _TEMPLATE.replace("__PAYLOAD__", json.dumps(payload, separators=(",", ":")))
        .replace("__TITLE__", path.parent.name or "ACS extract")
        .replace(
            "__SUBTITLE__",
            subtitle
            or f"{len(payload['features'])} features across "
            f"{len(payload['counties']):,} counties",
        )
        .replace("__EXTREMES__", str(EXTREME_ROWS))
        .replace("__TOOLTIP__", str(COUNTIES_PER_TOOLTIP))
        .replace(
            "__RELIABILITY__",
            json.dumps(reliability or {}, separators=(",", ":")),
        )
    )
    path.write_text(html, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Non-ACS columns: provenance for everything the joined dataset carries that
# `acs_spec` does not describe.
# ---------------------------------------------------------------------------
# The spec describes only the ACS features. The processed dataset also holds
# the geography and election variables, the share families, and the raw
# building blocks -- an audit tool that silently omits the variable
# someone is asking about is worse than no tool.
#
# Each entry is (section, source, universe, meaning).
#
# _GEO and _POL name the model's feature groups J and K verbatim, letter
# included, so the config-owned covariates listed here land in the same
# dropdown sections as the spec-managed features `_provenance` assigns to
# their groups (the raw E_20_* counts ride along with K).
_OUTCOME = "OUTCOME — never a predictor"
_BUILDING = "Building block / denominator"
_GEO = "J. Geography and Urbanity"
_POL = "K. Political Preference"
_POP = "Population context"

EXTRA_PROVENANCE: dict[str, tuple[str, str, str, str]] = {
    # --- geography, with no ACS equivalent
    "DENSITY": (
        _GEO,
        "TOTALPOP / ALAND",
        "County",
        "People per square metre of land area. A county-wide average, so a "
        "large county can look sparse while nearly everyone lives in one "
        "town -- URBANSHARE measures that instead.",
    ),
    "INTPTLAT": (
        _GEO,
        "TIGER internal point",
        "County",
        "Latitude of the county's internal point. Ranked top-three in 100% "
        "of splits in every specification of the current model.",
    ),
    "INTPTLON": (
        _GEO,
        "TIGER internal point",
        "County",
        "Longitude of the county's internal point. Runs to +178 because "
        "Aleutians West, AK sits across the antimeridian.",
    ),
    # --- elections (November 2020), with no ACS equivalent
    "VOTELEAN": (
        _POL,
        "E_20_PRES_REP, E_20_PRES_DEM",
        "Two-party presidential vote",
        "(Republican - Democratic) / total two-party vote, 2020 presidential. "
        "Positive is Republican-leaning. Counties with no two-party vote are "
        "null, which is how Puerto Rico leaves the model.",
    ),
    "NUMBEROFVOTERS": (
        _POL,
        "E_20_PRES_DEM + E_20_PRES_REP",
        "Two-party presidential vote",
        "COUNT of two-party votes cast in 2020. Largely a proxy for county "
        "size; correlated 0.98 with BACHDEG in the current model.",
    ),
    "TURNOUT": (
        _POL,
        "NUMBEROFVOTERS / VOTINGAGEPOP",
        "Voting-age population",
        "Two-party votes cast per voting-age resident, 2020 presidential. "
        "The one non-redundant ratio from the election columns: Democratic "
        "share of the two-party vote would be a perfectly monotone transform "
        "of VOTELEAN (Spearman -1.0) and so identical to a forest. Voting-age "
        "population includes non-citizens, so turnout runs low where many "
        "adults are ineligible. A few counties exceed 1.0 because VOTINGAGEPOP "
        "is a 2016-2020 ACS average while the votes are an actual November "
        "2020 count.",
    ),
    "E_20_PRES_DEM": (
        _POL,
        "election file",
        "Two-party presidential vote",
        "COUNT of Democratic votes, 2020 presidential.",
    ),
    "E_20_PRES_REP": (
        _POL,
        "election file",
        "Two-party presidential vote",
        "COUNT of Republican votes, 2020 presidential.",
    ),
    # --- outcomes: the within-Hispanic (of-Hisp) share family
    "Hisp SOR Alone Pct of Hisp": (
        _OUTCOME,
        "HSOR / HISPANIC",
        "Hispanic population (decennial)",
        "THE OUTCOME. Share of the county's Hispanic residents who selected "
        "Some Other Race alone on the 2020 Census.",
    ),
    "Hisp White Alone Pct of Hisp": (
        _OUTCOME,
        "HWHITE / HISPANIC",
        "Hispanic population (decennial)",
        "THE OUTCOME. Share of the county's Hispanic residents who selected "
        "White alone.",
    ),
    "Hisp White SOR Pct of Hisp": (
        _OUTCOME,
        "HWHITESOR / HISPANIC",
        "Hispanic population (decennial)",
        "THE OUTCOME. Share of the county's Hispanic residents who selected "
        "White and Some Other Race.",
    ),
    "Hisp White Pct of Hisp": (
        _OUTCOME,
        "HWHITEACOMBO / HISPANIC",
        "Hispanic population (decennial)",
        "Share of the county's Hispanic residents who selected White alone or "
        "in any combination (the alone-or-in-combination total).",
    ),
    # --- population context: the of-Pop share family (descriptive, not modeled)
    "Hisp Pct of Pop": (
        _POP,
        "HISPANIC / TOTALPOP",
        "Total population (decennial)",
        "Hispanic share of the county's total population, decennial. Context, "
        "not modeled and not an outcome: the outcomes are shares OF the "
        "Hispanic population, this is the share that IS Hispanic. The ACS "
        "equivalent, HISPSHARE, is the modeled predictor.",
    ),
    "Hisp SOR Alone Pct of Pop": (
        _POP,
        "HSOR / TOTALPOP",
        "Total population (decennial)",
        "Share of the county's TOTAL population that is Hispanic and selected "
        "Some Other Race alone. Descriptive; the modeled outcome is the "
        "of-Hisp version.",
    ),
    "Hisp White Alone Pct of Pop": (
        _POP,
        "HWHITE / TOTALPOP",
        "Total population (decennial)",
        "Share of the county's TOTAL population that is Hispanic and selected "
        "White alone. Descriptive; the modeled outcome is the of-Hisp version.",
    ),
    "Hisp White SOR Pct of Pop": (
        _POP,
        "HWHITESOR / TOTALPOP",
        "Total population (decennial)",
        "Share of the county's TOTAL population that is Hispanic and selected "
        "White and Some Other Race. Descriptive; the modeled outcome is the "
        "of-Hisp version.",
    ),
    "Hisp White Pct of Pop": (
        _POP,
        "HWHITEACOMBO / TOTALPOP",
        "Total population (decennial)",
        "Share of the county's TOTAL population that is Hispanic and selected "
        "White alone or in any combination. Descriptive; the modeled outcome "
        "is the of-Hisp version.",
    ),
    "largest": (
        _OUTCOME,
        "derived",
        "County",
        "Classification target: 1 = SOR alone is the largest Hispanic race "
        "choice, 2 = White + SOR, 3 = White alone.",
    ),
    "Most_SOR": (
        _OUTCOME,
        "derived",
        "County",
        "1 where SOR alone is the largest choice.",
    ),
    "Most_White": (
        _OUTCOME,
        "derived",
        "County",
        "1 where White alone is the largest choice.",
    ),
    "Most_White_SOR": (
        _OUTCOME,
        "derived",
        "County",
        "1 where White + SOR is the largest.",
    ),
    # --- population context: the size variables the weighted runs and the
    #     coverage diagnostics are read against
    "TOTALPOP": (
        _POP,
        "P1_001N",
        "Total population",
        "Decennial total population of the county.",
    ),
    "HISPANIC": (
        _POP,
        "P2_002N",
        "Total population",
        "Decennial Hispanic count. The denominator of every outcome and the "
        "weight in every population-weighted fit.",
    ),
    # --- building blocks
    "ACSTOTALPOP": (
        _BUILDING,
        "B01001_001E",
        "Total population",
        "ACS total population.",
    ),
    "ACSHISPANIC": (
        _BUILDING,
        "B03001_003E",
        "Total population",
        "ACS Hispanic count. The denominator of the origin shares.",
    ),
    "ALAND": (_BUILDING, "TIGER", "County", "Land area in square metres."),
    "AWATER": (_BUILDING, "TIGER", "County", "Water area in square metres."),
    "VOTINGAGEPOP": (
        _BUILDING,
        "B29001_001E",
        "Total population",
        "Voting-age population.",
    ),
}


# ---------------------------------------------------------------------------
# Driver: regenerate report/explorer.html from the v2 artifacts.
# ---------------------------------------------------------------------------
def write_explorer_page() -> Path:
    """Read the parquets and the reliability table, write the page."""
    data_dir = config.DATA_DIR / "national_counties"
    processed = pd.read_parquet(data_dir / "processed.parquet")
    raw = pd.read_parquet(data_dir / "raw.parquet")
    rel = pd.read_csv(data_dir / "report" / "feature_reliability.csv")

    # Coerce the raw frame (stored as API strings) for the raw-count views.
    value_cols = [c for c in raw.columns if c not in ("GEOID", "NAME")]
    raw[value_cols] = raw[value_cols].apply(pd.to_numeric, errors="coerce")

    # ACS raw columns only: the raw frame also carries the PL and DHC P2_*
    # columns, which would collide with the ACS codes in the count views.
    acs_raw = raw[["GEOID"] + [c for c in acs_spec.all_codes() if c in raw.columns]]

    # DHC counts under the bare code names the payload expects.
    prefix = dhc_vars.DHC_COLUMN_PREFIX
    dhc = raw[["GEOID"] + [prefix + c for c in dhc_vars.DHC_CODES]].rename(
        columns=lambda c: c.removeprefix(prefix)
    )

    quality = rel.rename(columns={"pct_cant_rule_out_zero": "pct_imprecise"})[
        ["feature", "pct_imprecise"]
    ]
    reliability = {
        row.feature: {
            "declined": int(row.n_missing_census_decline),
            "empty": int(row.n_missing_due_to_empty_denominator),
            "unpublished": int(row.n_missing_unpublished),
            "could_be_zero_pct": float(row.pct_cant_rule_out_zero),
        }
        for row in rel.itertuples()
    }

    n_features = sum(len(names) for _s, _t, names in manifest.MODEL_GROUPS.values())
    return write_explorer(
        processed,
        data_dir / "report" / "explorer.html",
        quality=quality,
        raw=acs_raw,
        dhc_counts=dhc,
        reliability=reliability,
        subtitle=f"{n_features} features across {len(processed):,} counties · v2 build",
    )


if __name__ == "__main__":
    out = write_explorer_page()
    print(f"wrote {out} ({out.stat().st_size / 1e6:.1f} MB)")
