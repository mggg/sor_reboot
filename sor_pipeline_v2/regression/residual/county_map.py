"""County maps of the modelled quantity: the outcome itself, or the residual.

`--column actual` maps the phenomenon -- the share of a county's Hispanic
residents reporting the target race choice -- on a sequential scale. This is
the presentable map: it states a fact about the country and needs no model
to read.

`--column residual` maps where the model misses, on a diverging scale about
zero. Treat it as a diagnostic, not a finding: residuals correlate about
+0.7 with the outcome itself (tree ensembles shrink predictions toward the
training mean, so they under-shoot high counties and over-shoot low ones),
which makes the residual map largely a muted copy of the outcome map.

Geometry comes from the pipeline's own cached TIGER download, simplified for
file size -- the same polygons the geometry audit verified against the
Gazetteer, so the map cannot disagree with the dataset it illustrates.

Two reading cautions are built in. The colour range is clipped at a
percentile so a handful of tiny-population counties cannot flatten the
scale, and `--min-hispanic` greys out counties whose share is computed over
too few people to mean anything.

Run: `python -m regression.residual.county_map [--run NAME] [--min-hispanic N]`.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import geopandas as gpd
import pandas as pd
import plotly.express as px

from utils import config

RESIDUAL_ROOT = config.DATA_DIR / "prediction" / "regression"
COUNTY_GEOMETRY = config.RAW_NATIONAL_DIR / "county_geometry_2020.parquet"
# ~1km at this latitude: keeps county outlines honest while cutting the
# embedded GeoJSON to a size a browser opens instantly.
SIMPLIFY_DEGREES = 0.01
# Clip the colour scale here so small-county noise cannot flatten the map.
COLOR_CLIP_PERCENTILE = 98


def load_residuals(run: str | None, min_hispanic: int) -> pd.DataFrame:
    """One run's residual table, filtered to counties worth mapping.

    Parameters
    ----------
    run : str or None
        Directory name (or any unique fragment of one) under the prediction
        directory; None takes the unstratified run.
    min_hispanic : int
        Drop counties below this Hispanic population.

    Returns
    -------
    pandas.DataFrame
        The residual rows, GEOID as string.

    Raises
    ------
    FileNotFoundError
        If no run matches.
    """
    candidates = sorted(RESIDUAL_ROOT.glob("residuals_*"))
    if run:
        candidates = [d for d in candidates if run in d.name]
    else:  # the unstratified run has no stratum suffix
        candidates = [d for d in candidates if d.name.count("_") == 2]
    if not candidates:
        raise FileNotFoundError(
            f"no residual run matching {run!r} under {RESIDUAL_ROOT}"
        )
    run_dir = candidates[0]
    table = pd.read_csv(next(run_dir.glob("residuals_*.csv")), dtype={"GEOID": str})
    table["run_name"] = run_dir.name.removeprefix("residuals_")
    return table[table["HISPANIC"] >= min_hispanic]


def county_geojson(geoids: pd.Series) -> dict:
    """Simplified polygons for the mapped counties, as GeoJSON keyed by GEOID.

    Parameters
    ----------
    geoids : pandas.Series
        The GEOIDs to include.

    Returns
    -------
    dict
        A GeoJSON FeatureCollection whose feature ids are GEOIDs.
    """
    counties = gpd.read_parquet(COUNTY_GEOMETRY)
    counties = counties[counties["GEOID"].isin(set(geoids))][["GEOID", "geometry"]]
    counties["geometry"] = counties.geometry.simplify(SIMPLIFY_DEGREES)
    return json.loads(counties.set_index("GEOID").to_json())


def plot_county_map(
    column: str = "actual",
    run: str | None = None,
    min_hispanic: int = 0,
    output_path: Path | None = None,
) -> Path:
    """Write the interactive county map of `column`.

    Parameters
    ----------
    column : str
        "actual" (the outcome, sequential scale) or "residual" (the model's
        miss, diverging about zero).
    run : str or None
        Which residual run supplies the rows.
    min_hispanic : int
        Population floor.
    output_path : Path or None
        Destination HTML; defaults into the prediction directory.

    Returns
    -------
    Path
        The HTML file written.
    """
    residuals = load_residuals(run, min_hispanic)
    if column == "residual":
        bound = float(residuals["residual"].abs().quantile(COLOR_CLIP_PERCENTILE / 100))
        scale, color_range = "RdBu", (-bound, bound)
        heading = "Where the model misses: out-of-fold residual by county"
        subtitle = "Blue = reports more of the target share than predicted; red = less."
    else:
        low, high = residuals[column].quantile(
            [1 - COLOR_CLIP_PERCENTILE / 100, COLOR_CLIP_PERCENTILE / 100]
        )
        scale, color_range = "Blues", (float(low), float(high))
        heading = "Some Other Race alone, share of each county's Hispanic residents"
        subtitle = "Darker = a larger share report SOR alone. 2020 Census."

    figure = px.choropleth(
        residuals,
        geojson=county_geojson(residuals["GEOID"]),
        locations="GEOID",
        color=column,
        color_continuous_scale=scale,
        range_color=color_range,
        scope="usa",
        hover_name="county",
        hover_data={
            "GEOID": True,
            "HISPANIC": ":,",
            "actual": ":.3f",
            "predicted": ":.3f",
            "residual": ":.3f",
        },
        labels={"residual": "Residual", "actual": "SOR share"},
        title=(
            heading
            + f"<br><sup>{subtitle} {len(residuals):,} counties"
            + (f", Hispanic population ≥ {min_hispanic:,}" if min_hispanic else "")
            + "</sup>"
        ),
    )
    figure.update_traces(marker_line_width=0.2, marker_line_color="white")
    figure.update_layout(margin={"r": 0, "t": 70, "l": 0, "b": 0})

    suffix = f"_min{min_hispanic}" if min_hispanic else ""
    output_path = output_path or RESIDUAL_ROOT / f"{column}_map{suffix}.html"
    figure.write_html(output_path)
    print(
        f"{len(residuals):,} counties mapped on '{column}' "
        f"({residuals['run_name'].iloc[0]}), range {color_range[0]:.3f} to "
        f"{color_range[1]:.3f} -> {output_path}"
    )
    return output_path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m regression.residual.county_map",
        description="County map of the outcome or the model residual.",
    )
    parser.add_argument("--column", choices=["actual", "residual"], default="actual")
    parser.add_argument(
        "--run", default=None, help="run-directory fragment, e.g. top-10pct"
    )
    parser.add_argument("--min-hispanic", type=int, default=0, metavar="N")
    parser.add_argument("--output", type=Path, default=None)
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    plot_county_map(args.column, args.run, args.min_hispanic, args.output)
