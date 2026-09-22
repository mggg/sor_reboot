"""Rendering for SHAP figures: the beeswarm and per-county waterfalls."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # file output only
import matplotlib.colors
import matplotlib.pyplot as plt
import pandas as pd
import shap
from matplotlib import patheffects
from matplotlib.axes import Axes

# State FIPS (a GEOID's first two digits) -> USPS abbreviation, for titles.
STATE_ABBREV = {
    "01": "AL",
    "02": "AK",
    "04": "AZ",
    "05": "AR",
    "06": "CA",
    "08": "CO",
    "09": "CT",
    "10": "DE",
    "11": "DC",
    "12": "FL",
    "13": "GA",
    "15": "HI",
    "16": "ID",
    "17": "IL",
    "18": "IN",
    "19": "IA",
    "20": "KS",
    "21": "KY",
    "22": "LA",
    "23": "ME",
    "24": "MD",
    "25": "MA",
    "26": "MI",
    "27": "MN",
    "28": "MS",
    "29": "MO",
    "30": "MT",
    "31": "NE",
    "32": "NV",
    "33": "NH",
    "34": "NJ",
    "35": "NM",
    "36": "NY",
    "37": "NC",
    "38": "ND",
    "39": "OH",
    "40": "OK",
    "41": "OR",
    "42": "PA",
    "44": "RI",
    "45": "SC",
    "46": "SD",
    "47": "TN",
    "48": "TX",
    "49": "UT",
    "50": "VT",
    "51": "VA",
    "53": "WA",
    "54": "WV",
    "55": "WI",
    "56": "WY",
    "72": "PR",
}


def county_label(geoid: str, county_names: pd.Series) -> str:
    state = STATE_ABBREV.get(geoid[:2], "??")
    return f"{county_names.get(geoid, geoid)} County, {state} (GEOID {geoid})"


def plot_beeswarm(explanation, title: str, output_path: Path) -> None:
    plt.figure()
    shap.plots.beeswarm(explanation, max_display=15, show=False)
    plt.title(title, fontsize=10)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close("all")


def plot_waterfall(
    county_explanation,
    county_title: str,
    actual: float,
    predicted: float,
    target_label: str,
    model_note: str,
    sample_note: str,
    output_path: Path,
) -> None:
    plt.figure()
    shap.plots.waterfall(county_explanation, max_display=12, show=False)
    _outline_white_bar_labels(plt.gca())
    plt.title(
        f"{county_title} — {target_label}\n"
        f"actual {actual:.1%} of Hispanic residents · "
        f"the model predicts {predicted:.1%}\n"
        f"{model_note} — {sample_note}",
        fontsize=10,
    )
    plt.figtext(
        0.5,
        -0.02,
        "gray number = this county's value of that feature · each bar = the "
        "feature's push on the prediction (red up, blue down)\n"
        "E[f(X)] = the model's average prediction over this sample (the "
        "baseline) · f(x) = its prediction for this county",
        ha="center",
        va="top",
        fontsize=8,
        color="0.35",
    )
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close("all")
    print(f"  {county_title}: waterfall written")


def _outline_white_bar_labels(ax: Axes) -> None:
    """shap prints bar values in white, which vanishes where a label overflows
    a short bar onto the background; it offers no styling hook, so outline."""
    for text in ax.texts:
        if matplotlib.colors.to_hex(text.get_color()) == "#ffffff":
            text.set_path_effects(
                [patheffects.withStroke(linewidth=1.5, foreground="0.45")]
            )
