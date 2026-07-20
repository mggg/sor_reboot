"""Plotting helpers: three-panel race-share scatters and the dual-graph map.

Migrated from `3hispaniccleanjune` cells 5 and 9 (and the near-identical
`statetractcleanedjune` cell 6). Functions take an explicit `save_path` so plots
can be written to files instead of relying on inline notebook rendering.
"""

from __future__ import annotations
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from sor_pipeline.utils import config, glossary

# Human-readable labels for the race-share columns, used in titles/axes.
RACE_SHARE_LABELS = {
    "Hisp SOR Alone PL Percent": "Hispanic: Some Other Race alone",
    "Hisp White SOR PL Percent": "Hispanic: White + Some Other Race",
    "Hisp White Alone PL Percent": "Hispanic: White alone",
}

X_LABEL = "Hispanic share of county population"
Y_LABEL = "Race-choice share of county population"

PLOTLY_RACE_COLORS = {
    1: "#1f77b4",
    2: "#2ca02c",
    3: "gold",
}  # tab:blue / tab:green / gold


def _race_label(col: str) -> str:
    """Pretty label for a race-share column (falls back to the raw name)."""
    return RACE_SHARE_LABELS.get(col, col)


def plot_three_panel_scatter(
    df, color_col: str, y_vars: list[str], log_color: bool = False, save_path=None
):
    """Three race-share scatterplots vs Hispanic share, colored by `color_col`.

    `log_color=True` reproduces the log-colored variant; otherwise the colormap is
    chosen per variable (bwr for VOTELEAN, etc.).

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing the data to plot. Must include columns for Hispanic share,
        the race share variables, and the color variable.
    color_col : str
        The name of the column in `df` to use for coloring the points.
    y_vars : list of str
        List of column names in `df` to plot on the y-axis. Each will be plotted in a separate panel.
    log_color : bool, optional
        If True, the color variable will be log-transformed for coloring. Default is False.
    save_path : str or Path, optional
        If provided, the path where the plot will be saved. If None, the plot will be displayed inline. Default is None.

    """
    fig = plt.figure(figsize=(18, 5))
    gs = gridspec.GridSpec(1, 4, width_ratios=[1, 1, 1, 0.05])

    axes = [fig.add_subplot(gs[i]) for i in range(3)]
    cax = fig.add_subplot(gs[3])

    x = df["Hisp PL Percent"].to_numpy()

    # Per-point color values. IMPORTANT: scatter() SILENTLY DROPS any point whose color
    # is NaN — the colormap's "bad" color does nothing for scatter (that only works for
    # imshow/pcolormesh). So we split the points: valid-color points go through the
    # colormap; missing-color points (log of a 0/negative covariate, or a missing value)
    # are drawn as a separate explicit-gray layer so they never vanish.
    vals = pd.to_numeric(df[color_col], errors="coerce")
    if log_color:
        c = np.log10(vals.where(vals > 0))  # non-positive -> NaN (avoids -inf)
        cmap = plt.cm.plasma
    elif color_col == "VOTELEAN":
        c = vals
        cmap = plt.cm.bwr
    elif color_col == "MEDAGE":
        c = vals.where(vals >= 0)  # negative census "jam" values -> NaN
        cmap = plt.cm.Greens
    else:
        c = vals
        cmap = plt.cm.plasma
    c = c.to_numpy()
    valid = np.isfinite(c)  # points with a usable color; the rest go in the gray layer

    # Shared y-axis limits across the three panels
    y_min = df[y_vars].min().min()
    y_max = df[y_vars].max().max()

    for ax, yname in zip(axes, y_vars):
        yv = pd.to_numeric(df[yname], errors="coerce").to_numpy()
        sc = ax.scatter(x[valid], yv[valid], c=c[valid], cmap=cmap, s=10)
        # missing-color points, drawn explicitly so scatter can't drop them
        ax.scatter(x[~valid], yv[~valid], color="0.6", s=10)
        ax.set_xlabel(X_LABEL)
        ax.set_title(_race_label(yname))
        ax.set_ylim(y_min, y_max)

    axes[0].set_ylabel(Y_LABEL)
    scale = "log₁₀ " if log_color else ""
    fig.colorbar(sc, cax=cax, label=f"{scale}{color_col}")

    # Explain the gray points (drawn only when some covariate values are 0/missing).
    if (~valid).any():
        from matplotlib.lines import Line2D

        missing_label = (
            f"{color_col} = 0 or missing" if log_color else f"{color_col} missing"
        )
        axes[0].legend(
            handles=[
                Line2D(
                    [0],
                    [0],
                    marker="o",
                    linestyle="",
                    color="0.6",
                    markersize=6,
                    label=missing_label,
                )
            ],
            loc="upper left",
            fontsize=8,
            framealpha=0.9,
        )

    fig.suptitle(
        f"Race-choice share vs. Hispanic share, colored by {scale}{color_col}",
        fontsize=14,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.95))  # leave room for the suptitle
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
    else:
        plt.show()


def plot_baseline_scatter(df, save_path=None):
    """Baseline three-panel scatter: each race share vs Hispanic share (uncolored)."""
    fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharex=True, sharey=True)

    x = df["Hisp PL Percent"]
    y_vars = [
        "Hisp SOR Alone PL Percent",
        "Hisp White SOR PL Percent",
        "Hisp White Alone PL Percent",
    ]
    for ax, col in zip(axes, y_vars):
        ax.scatter(x, df[col], s=1)
        ax.set_title(_race_label(col))
        ax.set_xlabel(X_LABEL)

    axes[0].set_ylabel(Y_LABEL)
    fig.suptitle("Race-choice share vs. Hispanic share (by county)", fontsize=14)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
    else:
        plt.show()


DOMINANT_RACE_COLORS = {1: "tab:blue", 2: "tab:green", 3: "gold"}
DOMINANT_RACE_LABELS = {
    1: "SOR alone",
    2: "White + SOR",
    3: "White alone",
}


def plot_logistic_coefficients(table, save_path=None):
    """Forest plot of univariate logistic coefficients (±95% CI), one panel per target.

    Reading it: each dot is a covariate's coefficient; the line is its 95% confidence
    interval; the dashed line at 0 means "no effect". Right of 0 = makes that race more
    likely to dominate, left = less likely. Blue = significant (p<0.05, CI clear of 0);
    gray = not. Coefficient *magnitudes* are NOT comparable across covariates (log vs.
    raw predictor scales) — read direction and significance, not bar-length vs bar-length.
    """
    targets = list(dict.fromkeys(table["target"]))
    fig, axes = plt.subplots(1, len(targets), figsize=(6 * len(targets), 7))
    if len(targets) == 1:
        axes = [axes]

    for ax, target in zip(axes, targets):
        sub = table[table["target"] == target].dropna(subset=["coef", "std_err"])
        sub = sub.sort_values("coef")
        ys = range(len(sub))
        for y, (_, row) in zip(ys, sub.iterrows()):
            sig = row["p_value"] < 0.05
            color = "tab:blue" if sig else "lightgray"
            ax.errorbar(
                row["coef"],
                y,
                xerr=1.96 * row["std_err"],
                fmt="o",
                color=color,
                ecolor=color,
                capsize=3,
                markersize=5,
            )
        ax.axvline(0, color="black", linestyle="--", linewidth=0.8)
        ax.set_yticks(list(ys))
        # Mark which predictors were log-transformed — it changes how the coefficient reads.
        labels = [
            f"{cov} (log)" if t == "log" else cov
            for cov, t in zip(sub["covariate"], sub["transform"])
        ]
        ax.set_yticklabels(labels)
        ax.set_title(target)
        ax.set_xlabel("Logistic coefficient (95% CI)")

    axes[0].set_ylabel("Covariate")
    fig.suptitle(
        "Univariate logistic coefficients by dominant-race target\n"
        "(blue = significant at p<0.05; gray = not; CI crossing 0 = no effect; "
        "'(log)' = predictor log-transformed; magnitudes not comparable across covariates)",
        fontsize=12,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
    else:
        plt.show()


def _state_outline_trace(states):
    xs, ys = [], []
    for geom in states.geometry:
        polys = geom.geoms if geom.geom_type == "MultiPolygon" else [geom]
        for p in polys:
            x, y = p.exterior.xy
            xs.extend(list(x) + [None])
            ys.extend(list(y) + [None])
    return go.Scatter(
        x=xs,
        y=ys,
        mode="lines",
        line=dict(color="#cccccc", width=0.7),
        hoverinfo="skip",
        showlegend=False,
    )


def plot_dual_graph(
    graph,
    save_path=None,
    region_name: str = "",
    unit_plural="counties",
    state_outlines=None,
    stats_note: str | None = None,
):
    """Draw the cluster dual graph: nodes at cluster centroids, colored by dominant race.

    Each node is a cluster positioned at its Web Mercator centroid (`x`/`y` carried
    onto the graph by build_dual_graph); edges connect bordering clusters. Node color
    encodes the `largest` race choice (1=SOR, 2=White+SOR, 3=White alone). `unit_plural`
    labels the underlying unit in the title ("counties" nationally, "tracts" per state).
    `stats_note` is an optional pre-built headline statistic (e.g. Moran's I) shown as
    its own subtitle line — the caller decides the content, this function just renders it.
    """
    nodes = list(graph.nodes())
    # Split edges by whether their endpoint clusters agree on dominant race choice:
    # matched edges are background connective tissue; mismatched edges ARE the
    # frontier where the map shifts color (the discordant pairs the half-edge
    # score summarizes).
    edge_x, edge_y = [], []  # endpoints agree
    frontier_x, frontier_y = [], []  # endpoints differ: race-choice boundary
    for u, v in graph.edges():
        seg_x = [graph.nodes[u]["x"], graph.nodes[v]["x"], None]
        seg_y = [graph.nodes[u]["y"], graph.nodes[v]["y"], None]
        if int(graph.nodes[u].get("largest", 0)) == int(
            graph.nodes[v].get("largest", 0)
        ):
            edge_x.extend(seg_x)
            edge_y.extend(seg_y)
        else:
            frontier_x.extend(seg_x)
            frontier_y.extend(seg_y)
    pops = [graph.nodes[n]["TOTALPOP"] for n in nodes]
    lo, hi = min(pops), max(pops)
    span = (hi - lo) or 1  # guard against all-equal populations
    diameter = lambda p: (20 + 180 * (p - lo) / span) ** 0.5

    traces = []
    if state_outlines is not None:
        traces.append(_state_outline_trace(state_outlines))
    traces.append(
        go.Scatter(
            x=edge_x,
            y=edge_y,
            mode="lines",
            line=dict(color="lightgray", width=0.3),
            hoverinfo="skip",
            showlegend=False,
        )
    )
    if frontier_x:
        # Dark red: deliberately outside the node palette so the boundary reads as
        # belonging to neither side. Drawn after the matched edges, before nodes.
        traces.append(
            go.Scatter(
                x=frontier_x,
                y=frontier_y,
                mode="lines",
                line=dict(color="#8b0000", width=0.8),
                name="race-choice boundary",
                hoverinfo="skip",
            )
        )

    for code, label in DOMINANT_RACE_LABELS.items():
        group = [n for n in nodes if int(graph.nodes[n].get("largest", 0)) == code]
        # print(graph.nodes[0])
        traces.append(
            go.Scatter(
                x=[graph.nodes[n]["x"] for n in group],
                y=[graph.nodes[n]["y"] for n in group],
                mode="markers",
                name=label,
                marker=dict(
                    color=PLOTLY_RACE_COLORS[code],
                    size=[diameter(graph.nodes[n]["TOTALPOP"]) for n in group],
                ),
                text=[
                    f"<b>{graph.nodes[n]['NAME']}, {','.join(glossary.FIPS_TO_STATE.get(fp, 'Unknown') for fp in graph.nodes[n]['STATEFP'].split(','))}</b><br>"
                    f"Total population: {graph.nodes[n]['TOTALPOP']:,.0f}<br>"
                    f"Hispanic Population: {graph.nodes[n]['HISPANIC']:,.0f} ({graph.nodes[n]['HISPANIC']/graph.nodes[n]['TOTALPOP']:.1%})<br>"
                    f"White + SOR: {graph.nodes[n]['HWHITESOR']:,.0f} ({graph.nodes[n]['HWHITESOR']/graph.nodes[n]['HISPANIC']:.1%})<br>"
                    f"White alone: {graph.nodes[n]['HWHITE']:,.0f} ({graph.nodes[n]['HWHITE']/graph.nodes[n]['HISPANIC']:.1%})<br>"
                    f"SOR alone: {graph.nodes[n]['HSOR']:,.0f} ({graph.nodes[n]['HSOR']/graph.nodes[n]['HISPANIC']:.1%})<br>"
                    for n in group
                ],
                hovertemplate="%{text}<extra></extra>",
                hoverlabel=dict(
                    bgcolor="white",
                    bordercolor="lightgray",
                    font=dict(size=13, color="#333"),
                    align="left",
                ),
            )
        )

    fig = go.Figure(traces)
    fig.update_yaxes(scaleanchor="x", visible=False)
    fig.update_xaxes(visible=False)

    warning = (
        f" Warning: fewer than {config.MIN_SPATIAL_UNITS} clusters; "
        "Moran and CAPY results may be unreliable."
        if len(nodes) < config.MIN_SPATIAL_UNITS
        else ""
    )

    fig.update_layout(
        # Set a global font family so the title, subtitle, and legend all match
        font=dict(family="Arial, Helvetica, sans-serif"),
        title=dict(
            # Bold the main title and remove the trailing <br> which caused awkward spacing
            text=f"<b>Dominant Hispanic Race Choice by Cluster in {' '.join(word.capitalize() if word.lower() != 'us' else word.upper() for word in region_name.split('_'))}</b>",
            font=dict(size=20),
            subtitle=dict(
                text=(
                    f"Hover over a dot for cluster details.<br>"
                    f"Each dot = a cluster of one or more {unit_plural}*, sized by "
                    f"total population; edges join bordering clusters.<br>"
                    + (f"{stats_note}<br>" if stats_note else "")
                    # Use HTML span to visually de-emphasize the methodology footnote
                    + f"<span style='color: #666666; font-size: 11px;'>"
                    f"*Counties with fewer than {config.MIN_CLUSTER_HISPANIC} Hispanic "
                    f"residents are merged with neighbors. Total clusters: {len(nodes)}. "
                    f"Median population per cluster: {np.median(pops):,.0f}."
                    f" {warning}"
                    # The ** marker lives in stats_note (built by the runner), so only
                    # emit its footnote when there is a stats line to reference it.
                    + (
                        "<br>**Small-population clustering: race-choice percentages "
                        "are computed on those merged clusters rather than raw "
                        "counties, so tiny-population noise doesn't drown out the "
                        "spatial pattern being measured."
                        if stats_note
                        else ""
                    )
                    + f"</span>"
                ),
                font=dict(size=13, color="#333333"),
            ),
        ),
        # Top margin fits the subtitle block; the stats line + its ** footnote add two rows.
        margin=dict(t=145 if stats_note else 110, b=0, l=0, r=0),
        legend=dict(
            title="<b>Dominant Hispanic Race Choice</b>",
            x=0.01,
            xanchor="left",
            y=0.01,
            yanchor="bottom",
            bgcolor="rgba(255,255,255,0.9)",  # Made slightly more opaque for readability
            bordercolor="#e5e5e5",  # Added a subtle border to the legend
            borderwidth=1,
        ),
        plot_bgcolor="white",
    )

    fig.write_html(save_path)
