"""Spatial analysis: small-population clustering, Moran's I, CAPY half-edge, dual graph.

Migrated from `3hispaniccleanjune` cell 7 and `statetractcleanedjune` cell 8 (the
two largest cells, ~400+ lines each and nearly identical between notebooks).
Centralizing them here removes that duplication.
"""

from __future__ import annotations
from pathlib import Path
from sor_pipeline.utils.config import EXCLUDE_STATES, REGIONS
import pandas as pd
import geopandas as gpd
import gerrychain
import numpy as np
from collections import Counter, deque
from libpysal.weights import Rook
from esda.moran import Moran
from esda.smoothing import Empirical_Bayes
import plotly.graph_objects as go
import sys


def prepare_contiguous(df: pd.DataFrame) -> pd.DataFrame:
    """Drop non-contiguous states/territories — spatial stats need touching neighbors."""
    df = df.copy()
    df["STATEFP"] = df["GEOID"].str[:2]
    gdf = df[~df["STATEFP"].isin(EXCLUDE_STATES)].copy()
    return gdf.reset_index(drop=True)


def select_region(df: pd.DataFrame, state_fips):
    """Select a region of interest (contiguous, Alaska, Hawaii, Puerto Rico)."""
    df = df.copy()
    df["STATEFP"] = df["GEOID"].str[:2]
    if state_fips is None:
        claimed = {f for fips in REGIONS.values() if fips is not None for f in fips}
        keep = ~df["STATEFP"].isin(claimed) | df["STATEFP"].isin(EXCLUDE_STATES)
    else:
        keep = df["STATEFP"].isin(state_fips)
    return df[keep].copy().reset_index(drop=True)


# --- (A) Small-population clustering -----------------------------------------


def is_rook_neighbor(g1, g2) -> bool:
    """Return True if two geometries share a boundary segment (rook adjacency)."""
    inter = g1.intersection(g2.boundary)
    return inter.length > 0


def get_neighbors(idx, sindex, gdf) -> list[int]:
    """Return positional indices of rook-adjacent geometries for unit ``idx``."""
    geom = gdf.geometry.iloc[idx]
    possible = list(sindex.intersection(geom.bounds))
    return [
        i for i in possible if i != idx and is_rook_neighbor(geom, gdf.geometry.iloc[i])
    ]


def cluster_small_population(gdf: pd.DataFrame, min_pop: int):
    """Grow regions around small-Hispanic units until each clears `min_pop`.

    Units already at/above `min_pop` stand alone; `min_pop=0` therefore disables
    clustering entirely (every unit is its own cluster). Returns the cluster label
    per row. Zero-Hispanic units are deferred and reassigned to their most common
    bordering cluster afterward.
    """
    # spatial index for fast neighbor lookups
    sindex = gdf.sindex

    visited = set()
    clusters = []
    cluster_id = 0
    cluster_labels = [-1] * len(gdf)
    # Process the smallest-Hispanic tracts first so they get absorbed
    order = np.argsort(gdf["HISPANIC"].values)

    for i in order:
        if i in visited:
            continue

        pop = gdf.loc[i, "HISPANIC"]

        # Defer zero-Hispanic tracts; assign them after clustering
        if pop == 0:
            continue

        # Already large enough to stand alone
        if pop >= min_pop:
            cluster_labels[i] = cluster_id
            visited.add(i)
            clusters.append([i])
            cluster_id += 1
            continue

        # Otherwise grow a region outward until it reaches MIN_POP
        cluster = [i]
        visited.add(i)
        total_pop = pop
        frontier = get_neighbors(i, sindex, gdf)

        while total_pop < min_pop and frontier:
            nxt = frontier.pop(0)
            if nxt in visited:
                continue

            nxt_pop = gdf.loc[nxt, "HISPANIC"]
            if nxt_pop == 0:  # don't grow into zero-pop tracts
                continue

            cluster.append(nxt)
            visited.add(nxt)
            total_pop += nxt_pop
            frontier.extend(get_neighbors(nxt, sindex, gdf))

        for idx in cluster:
            cluster_labels[idx] = cluster_id
        clusters.append(cluster)
        cluster_id += 1

    # --- Assign the deferred zero-Hispanic tracts ---
    zero_idxs = set(
        gdf.index[gdf["HISPANIC"] == 0]
    )  # Get indices of zero-Hispanic tracts
    visited_zero = set()  # Track visited zero-Hispanic tracts
    zero_components = []  # List to hold connected components of zero-Hispanic tracts

    # Group contiguous zero-pop tracts into connected components (BFS)
    for idx in zero_idxs:
        if idx in visited_zero:
            continue  # Skip already visited tracts

        component = []  # Track the current connected component
        queue = deque(
            [idx]
        )  # To-do list of tracts to explore (a deque is a double-ended queue, which is efficient for popping from the left)
        visited_zero.add(idx)

        while queue:
            current = (
                queue.popleft()
            )  # popleft takes from the front, which makes it a breadth-first (first-in-first-out) search, meaning it explores all neighbors of a tract before moving on to the next level of neighbors.
            component.append(current)
            for nbr in get_neighbors(current, sindex, gdf):
                if nbr in zero_idxs and nbr not in visited_zero:
                    visited_zero.add(nbr)
                    queue.append(nbr)

        zero_components.append(component)

    # Attach each zero-pop component to its most common bordering cluster
    # Attach each blob to a real, populated cluster by majority vote of its neighbors.
    # If a blob is isolated, attach it to the nearest cluster centroid.
    for component in zero_components:
        neighboring_clusters = []
        for tract in component:
            for nbr in get_neighbors(tract, sindex, gdf):
                nbr_cluster = cluster_labels[nbr]
                # ignore unassigned (-1) and within-component neighbors
                if nbr_cluster != -1 and nbr not in component:
                    neighboring_clusters.append(nbr_cluster)

        if neighboring_clusters:
            assigned_cluster = Counter(neighboring_clusters).most_common(1)[0][0]
            for tract in component:
                cluster_labels[tract] = assigned_cluster
        else:
            # Isolated zero-pop island: attach to the nearest cluster centroid
            valid = gdf[np.array(cluster_labels) != -1]
            component_geom = gdf.loc[component].geometry.union_all()
            nearest_idx = valid.distance(component_geom.centroid).idxmin()
            assigned_cluster = cluster_labels[nearest_idx]
            for tract in component:
                cluster_labels[tract] = assigned_cluster
    return cluster_labels


def dissolve_clusters(gdf, cluster_labels):
    """Dissolve units into clusters, summing counts, and compute cluster-level rates."""
    gdf = gdf.copy()
    gdf["cluster_id"] = cluster_labels
    # print(gdf.columns.tolist())
    # sys.exit(0)
    clustered = gdf.dissolve(
        by="cluster_id",
        aggfunc={
            "TOTALPOP": "sum",
            "HISPANIC": "sum",
            "HSOR": "sum",
            "H_N_SOR": "sum",
            "HWHITE": "sum",
            "H_N_WHITE": "sum",
            "HWHITESOR": "sum",
            "H_N_WHITESOR": "sum",
            "HWHITEACOMBO": "sum",
            "H_N_WHITEACOMBO": "sum",
            "E_20_PRES_DEM": "sum",
            "E_20_PRES_REP": "sum",
            "NAME": lambda x: ", ".join(x),  # Concatenate county names for reference
            "STATEFP": lambda x: ", ".join(
                x.unique()
            ),  # Concatenate state FIPS for reference
        },
    )
    clustered["NONHISPANIC"] = clustered["TOTALPOP"] - clustered["HISPANIC"]

    # cluster-level rates for Moran's I
    clustered["pct_HSOR"] = clustered["HSOR"] / clustered["HISPANIC"]
    clustered["pct_HWhiteSOR"] = clustered["HWHITESOR"] / clustered["HISPANIC"]
    clustered["pct_HWHITE"] = clustered["HWHITE"] / clustered["HISPANIC"]
    clustered["pct_HWHITEACOMBO"] = clustered["HWHITEACOMBO"] / clustered["HISPANIC"]
    clustered["pct_HISP"] = clustered["HISPANIC"] / clustered["TOTALPOP"]
    clustered["pct_DEM"] = clustered["E_20_PRES_DEM"] / (
        clustered["E_20_PRES_DEM"] + clustered["E_20_PRES_REP"] + 1
    )
    return clustered


def build_rook_weights(clustered):
    """Drop islands (units with no neighbors) and return (clustered_without_islands, weights).

    Islands break Moran's I, and the dual graph should be built on the same
    island-free units — so this prep is shared by both rather than buried in one.
    The returned weights are row-standardized (``transform="r"``).
    """
    clustered = clustered.reset_index(drop=True)
    if len(clustered) <= 1:
        return clustered, None  # Handle empty GeoDataFrame gracefully
    w = Rook.from_dataframe(clustered, use_index=False)
    clustered = clustered.drop(index=w.islands).reset_index(drop=True)
    if len(clustered) <= 1:
        return clustered, None  # Handle empty GeoDataFrame gracefully
    w = Rook.from_dataframe(
        clustered, use_index=False
    )  # rebuild without the dropped islands
    w.transform = "r"  # row-standardize
    return clustered, w


def morans_i(clustered, w, columns: list[str]):
    """Compute Moran's I (+ permutation p-value) for each column under weights ``w``.

    Returns ``{column: {"I": ..., "EI": ..., "p_sim": ...}}`` where ``EI`` is the
    expected value under the null, -1/(n-1). Expects island-free data and
    pre-built weights from ``build_rook_weights``.
    """
    results = {}
    for col in columns:
        mi = Moran(clustered[col], w)
        results[col] = {"I": mi.I, "EI": mi.EI, "p_sim": mi.p_sim}
    return results


def raw_moran(gdf, count_col: str, base_col: str):
    """Moran's I on the *unsmoothed* rate ``count_col / base_col`` — the naive baseline.

    No clustering, no smoothing: the rate straight off the raw units. This is the
    reference both denoising strategies improve on. Small denominators make these
    rates noisy, and that noise (being spatially random) attenuates Moran's I toward
    0 — so expect this to come in below the clustered/Empirical-Bayes versions.
    Same units + weights as ``empirical_bayes_moran``, so the two are directly
    comparable and isolate the effect of smoothing. Returns ``{"I", "EI", "p_sim"}``.
    """
    gdf = gdf.copy()
    gdf["_raw_rate"] = gdf[count_col] / gdf[base_col]
    w = Rook.from_dataframe(gdf, use_index=False)
    w.transform = "r"
    mi = Moran(gdf["_raw_rate"], w)
    return {"I": mi.I, "EI": mi.EI, "p_sim": mi.p_sim}


def empirical_bayes_moran(gdf, count_col: str, base_col: str):
    """Empirical-Bayes-smooth ``count_col / base_col``, then Moran's I on the result.

    The alternative to clustering (strategy B): instead of merging small units,
    shrink each unit's noisy rate toward the global mean (harder for small samples),
    then measure spatial autocorrelation on the smoothed rate. ``gdf`` should already
    be restricted to units with a positive denominator. Returns ``{"I", "EI", "p_sim"}``.
    """
    gdf = gdf.copy()
    eb = Empirical_Bayes(gdf[count_col].values, gdf[base_col].values)
    gdf["_eb_rate"] = eb.r
    w = Rook.from_dataframe(gdf, use_index=False)
    w.transform = "r"
    mi = Moran(gdf["_eb_rate"], w)
    return {"I": mi.I, "EI": mi.EI, "p_sim": mi.p_sim}


# --- CAPY half-edge inner-product operators ----------------------------------


def _angle_1(graph: gerrychain.Graph, x_col: str, y_col: str):
    """Return the (node-term, edge-term) pair for the ``<x, y>`` operator.

    Computes the topological inner product between two count columns on a dual graph.
    The node term is the sum of the products of the counts at each node, and the edge term
    is the sum of the products of the counts at each pair of adjacent nodes. This operator
    is used in the CAPY half-edge clustering score to measure the spatial clustering of two complementary count columns.
    """
    node_term = 0
    edge_term = 0
    for node in graph.nodes():
        node_term += int(graph.nodes[node][x_col]) * int(graph.nodes[node][y_col])
    for u, v in graph.edges():
        edge_term += int(graph.nodes[u][x_col]) * int(graph.nodes[v][y_col])
        edge_term += int(graph.nodes[v][x_col]) * int(graph.nodes[u][y_col])
    return node_term, edge_term


def angle_1(graph: gerrychain.Graph, x_col: str, y_col: str, lam: float = 1) -> float:
    """The ``<x, y>`` operator from the CAPY paper.

    ``lam=None`` returns only the node term; otherwise ``lam * node_term + edge_term``.
    """
    node_term, edge_term = _angle_1(graph, x_col, y_col)
    if lam is None:
        return node_term
    return (lam * node_term) + edge_term


def _angle_2(graph: gerrychain.Graph, x_col: str, y_col: str):
    """Return the (node-term, edge-term) pair for the ``<<x, y>>`` operator."""
    node_term = 0
    edge_term = 0
    for node in graph.nodes():
        node_term += int(graph.nodes[node][x_col]) * int(graph.nodes[node][y_col]) - (
            (int(graph.nodes[node][x_col]) + int(graph.nodes[node][y_col])) * 0.5
        )
    for u, v in graph.edges():
        edge_term += int(graph.nodes[u][x_col]) * int(graph.nodes[v][y_col])
        edge_term += int(graph.nodes[v][x_col]) * int(graph.nodes[u][y_col])
    return node_term, edge_term


def angle_2(graph: gerrychain.Graph, x_col: str, y_col: str, lam: float = 1) -> float:
    """The ``<<x, y>>`` operator from the CAPY paper.

    ``lam=None`` returns only the node term; otherwise ``0.5 * (lam * node_term + edge_term)``.
    """
    node_term, edge_term = _angle_2(graph, x_col, y_col)
    if lam is None:
        return node_term
    return 0.5 * ((lam * node_term) + edge_term)


def half_edge(
    graph: gerrychain.Graph, x_col: str, y_col: str, lam: float = 1, func=angle_1
) -> float:
    """CAPY half-edge clustering score between two complementary count columns.

    ``x_col`` and ``y_col`` are a count and its complement (e.g. ``HSOR`` / ``H_N_SOR``).
    Higher score (~[0, 1]) means that group is more spatially clustered.
    """
    x_x = func(graph, x_col, x_col, lam=lam)
    x_y = func(graph, x_col, y_col, lam=lam)
    y_y = func(graph, y_col, y_col, lam=lam)
    return 0.5 * ((x_x / (x_x + x_y)) + (y_y / (y_y + x_y)))


# --- Dual graph --------------------------------------------------------------


def build_dual_graph(clustered: gpd.GeoDataFrame, save_path: str) -> gerrychain.Graph:
    """Assign per-cluster dominant race, build the gerrychain dual graph, save + reload it.

    Nodes = clusters (carrying their counts + a ``largest`` race label + ``x``/``y``
    centroid coords for plotting); edges = shared borders. The graph is written to
    ``save_path`` as JSON and reloaded (gerrychain round-trips through disk).
    """
    clustered = clustered.copy()

    # project to Web Mercator and record centroid coords (node positions for plotting)
    clustered = clustered.to_crs(epsg=3857)
    clustered["x"] = clustered.geometry.centroid.x
    clustered["y"] = clustered.geometry.centroid.y

    # dominant Hispanic race choice per cluster: 1 = SOR, 2 = White+SOR, 3 = White alone.
    # (argmax of the three counts with the notebook's tie-breaking.)
    hsor, hws, hw = clustered["HSOR"], clustered["HWHITESOR"], clustered["HWHITE"]
    conditions = [
        (hsor >= hw) & (hsor >= hws),  # SOR is largest -> 1
        (hw > hsor) & (hw >= hws),  # White alone is largest -> 3
    ]
    clustered["largest"] = np.select(conditions, [1, 3], default=2)

    print("Clustered head: ", clustered.columns.tolist())
    # gerrychain can't serialize NaNs, and half_edge casts these to int — fill them all.
    relevant_columns = [
        "HSOR",
        "H_N_SOR",
        "HWHITESOR",
        "H_N_WHITESOR",
        "HWHITE",
        "H_N_WHITE",
        "HWHITEACOMBO",
        "H_N_WHITEACOMBO",
        "HISPANIC",
        "NONHISPANIC",
        "E_20_PRES_DEM",
        "E_20_PRES_REP",
        "largest",
        "NAME",
        "STATEFP",
    ]
    clustered[relevant_columns] = clustered[relevant_columns].fillna(0)
    print(clustered.head(3))
    print(clustered.describe(include="all").T)

    save_path = Path(save_path)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    graph = gerrychain.Graph.from_geodataframe(clustered)
    graph.to_json(str(save_path))
    return gerrychain.Graph.from_json(str(save_path))
