"""
McDonald's Tokyo — Site Selection Pipeline

Discovers dining-demand clusters across Tokyo with HDBSCAN, scores a dense
candidate grid, and applies greedy diversity selection to find the top N
candidate locations for new outlets.

HDBSCAN noise points are reassigned to their nearest cluster centroid so
sparse-but-active areas (e.g. Shirokane) still surface as low-confidence
candidates instead of being discarded.

Entry points
------------
  python site_selection.py     — saves output/top_candidates.csv
  python app_interactive.py    — saves output/interactive_map.html  (interactive)
"""

import numpy as np
import pandas as pd
import hdbscan
from pathlib import Path
from sklearn.neighbors import BallTree

import folium
import folium.plugins

from config_modeling import (
    BBOX, HDBSCAN_PARAMS, GRID_STEP_DEG,
    MIN_DIST_TO_OWN_KM, MAX_DIST_TO_COMP_KM,
    SCORE_WEIGHTS, TOP_N_SITES, MIN_SPREAD_KM,
    OUTPUT_DIR, OUTPUT_CSV, COMPETITOR_SOURCES,
)
from spatial_features import build_balltree, add_nearest_distance

OWN_BRAND = "マクドナルド"
NOISE_MEMBERSHIP = 0.50   # default confidence weight for sparse-area candidates

CATEGORY_STYLE = {
    "burger":   {"colour": "#E65100", "radius": 5, "opacity": 0.80,
                 "label": "Burger chains (direct, w=1.0)"},
    "teishoku": {"colour": "#6A1B9A", "radius": 4, "opacity": 0.60,
                 "label": "Teishoku chains (indirect, w=0.5)"},
    "family":   {"colour": "#00695C", "radius": 4, "opacity": 0.50,
                 "label": "Family restaurants (indirect, w=0.3)"},
}


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def _parse_reviews(s) -> int:
    """'215 人' → 215, missing/unparseable → 0."""
    if pd.isna(s):
        return 0
    tok = str(s).split()[0].replace(",", "")
    return int(tok) if tok.isdigit() else 0


def load_all_restaurants() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load every restaurant across all competitor tiers into one pool.

    HDBSCAN uses raw review_count (not weighted) so all restaurants
    contribute equally to the demand signal.

    Returns
    -------
    all_df  : every restaurant (McDonald's + competitors)
    own_df  : McDonald's only
    comp_df : competitors only
    """
    frames = []
    for category, cfg in COMPETITOR_SOURCES.items():
        df = pd.read_csv(cfg["path"]).dropna(subset=["latitude", "longitude"])
        df["review_count"] = df["reviews"].apply(_parse_reviews)
        df["category"]     = category
        df["comp_weight"]  = cfg["weight"]
        df["is_own"]       = False
        if "exclude_brand" in cfg:
            df.loc[df["brand"] == cfg["exclude_brand"], "is_own"] = True
        frames.append(df)

    all_df  = pd.concat(frames, ignore_index=True)
    own_df  = all_df[all_df["is_own"]].copy().reset_index(drop=True)
    comp_df = all_df[~all_df["is_own"]].copy().reset_index(drop=True)
    comp_df["popularity"] = comp_df["review_count"] * comp_df["comp_weight"]
    return all_df, own_df, comp_df


# ---------------------------------------------------------------------------
# Candidate grid
# ---------------------------------------------------------------------------

def generate_candidate_grid() -> pd.DataFrame:
    lats = np.arange(BBOX["lat_min"], BBOX["lat_max"], GRID_STEP_DEG)
    lons = np.arange(BBOX["lon_min"], BBOX["lon_max"], GRID_STEP_DEG)
    lat_g, lon_g = np.meshgrid(lats, lons)
    return pd.DataFrame({"latitude": lat_g.ravel(), "longitude": lon_g.ravel()})


# ---------------------------------------------------------------------------
# HDBSCAN
# ---------------------------------------------------------------------------

def fit_demand_hdbscan(all_df: pd.DataFrame) -> hdbscan.HDBSCAN:
    """
    Fit HDBSCAN on all restaurants weighted by review_count via row replication.
    High-review locations exert more influence on cluster formation.
    """
    q25     = max(1, int(all_df["review_count"].quantile(0.25)))
    repeats = (all_df["review_count"] / q25).round().clip(lower=1, upper=10).astype(int)
    weighted_df = all_df.loc[all_df.index.repeat(repeats)].reset_index(drop=True)
    coords_rad  = np.radians(weighted_df[["latitude", "longitude"]].values)
    print(f"  Weighted pool: {len(weighted_df):,} points "
          f"(Q25 = {q25} reviews → 1 repeat; higher-review get up to 10×)")
    clusterer = hdbscan.HDBSCAN(**HDBSCAN_PARAMS)
    clusterer.fit(coords_rad)
    return clusterer


# ---------------------------------------------------------------------------
# Cluster statistics (noise reassigned to nearest centroid)
# ---------------------------------------------------------------------------

def _assign_noise_to_nearest(
    coords_rad: np.ndarray,
    labels: np.ndarray,
    centroids: pd.DataFrame,
) -> np.ndarray:
    """Replace label=-1 (noise) with the nearest cluster centroid's label."""
    noise_mask = labels == -1
    if noise_mask.sum() == 0:
        return labels.copy()
    centroid_coords_rad = np.radians(centroids[["latitude", "longitude"]].values)
    tree = BallTree(centroid_coords_rad, metric="haversine")
    _, nearest_idx = tree.query(coords_rad[noise_mask], k=1)
    corrected = labels.copy()
    corrected[noise_mask] = centroids.index.values[nearest_idx.flatten()]
    return corrected


def compute_cluster_stats(
    all_df: pd.DataFrame,
    clusterer,
) -> tuple[pd.DataFrame, np.ndarray, pd.DataFrame]:
    """
    Assign every restaurant to a demand cluster, including noise restaurants.

    Returns
    -------
    stats     : per-cluster DataFrame (total_demand, mcd_count, mcd_gap …)
    labels    : corrected cluster label per restaurant row
    centroids : cluster centroid lat/lon
    """
    coords_rad = np.radians(all_df[["latitude", "longitude"]].values)
    raw_labels, _ = hdbscan.approximate_predict(clusterer, coords_rad)

    df_temp = all_df.copy()
    df_temp["cluster"] = raw_labels
    centroids = (
        df_temp[df_temp["cluster"] >= 0]
        .groupby("cluster")[["latitude", "longitude"]]
        .mean()
    )

    corrected = _assign_noise_to_nearest(coords_rad, raw_labels, centroids)
    df_temp["cluster"] = corrected

    n_noise = int((raw_labels == -1).sum())
    print(f"  Noise restaurants reassigned: {n_noise} → nearest centroid")

    stats = df_temp.groupby("cluster").agg(
        total_demand  = ("review_count", "sum"),
        n_restaurants = ("review_count", "count"),
        mcd_count     = ("is_own",       "sum"),
    )
    stats["mcd_saturation"] = stats["mcd_count"] / stats["n_restaurants"]
    stats["mcd_gap"]        = 1.0 - stats["mcd_saturation"]
    return stats, corrected, centroids


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def score_candidates(
    candidates:    pd.DataFrame,
    own_df:        pd.DataFrame,
    comp_df:       pd.DataFrame,
    clusterer,
    cluster_stats: pd.DataFrame,
    centroids:     pd.DataFrame,
    own_tree,
    comp_tree,
) -> pd.DataFrame:
    cands = candidates.copy()

    cands["dist_to_own_km"]  = add_nearest_distance(cands, own_df,  "d", own_tree)
    cands["dist_to_comp_km"] = add_nearest_distance(cands, comp_df, "d", comp_tree)

    cands_rad = np.radians(cands[["latitude", "longitude"]].values)
    raw_labels, strengths = hdbscan.approximate_predict(clusterer, cands_rad)
    raw_membership_arr = strengths.astype(float)

    corrected = _assign_noise_to_nearest(cands_rad, raw_labels, centroids)
    membership = np.where(raw_labels == -1, NOISE_MEMBERSHIP, raw_membership_arr)

    cands["cluster_label"]       = corrected
    cands["membership_strength"] = membership
    cands["was_noise"]           = raw_labels == -1
    cands["raw_membership"]      = raw_membership_arr

    mask = (
        (cands["dist_to_own_km"]  >= MIN_DIST_TO_OWN_KM) &
        (cands["dist_to_comp_km"] <= MAX_DIST_TO_COMP_KM)
    )
    filt = cands[mask].copy().reset_index(drop=True)
    if filt.empty:
        raise RuntimeError("No candidates survived filtering — check BBOX / thresholds.")

    filt = filt.join(
        cluster_stats[["total_demand", "mcd_gap", "mcd_count", "n_restaurants"]],
        on="cluster_label",
    )

    demand_max = filt["total_demand"].max()
    filt["cluster_demand_score"] = filt["total_demand"] / demand_max
    filt["mcd_gap_score"]        = filt["mcd_gap"]
    filt["distance_buffer"]      = filt["dist_to_own_km"].clip(upper=2.0) / 2.0

    filt["base_score"] = (
        SCORE_WEIGHTS["cluster_demand"]  * filt["cluster_demand_score"] +
        SCORE_WEIGHTS["mcd_gap"]         * filt["mcd_gap_score"]        +
        SCORE_WEIGHTS["distance_buffer"] * filt["distance_buffer"]
    )

    raw_score     = filt["base_score"] * filt["membership_strength"]
    filt["score"] = raw_score / raw_score.max()

    return filt.sort_values("score", ascending=False).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Greedy diversity selection
# ---------------------------------------------------------------------------

def greedy_diversity_select(
    scored_df: pd.DataFrame,
    n: int,
    min_spread_km: float,
) -> pd.DataFrame:
    """Pick the top-n candidates ensuring each site is ≥ min_spread_km apart."""
    coords    = np.radians(scored_df[["latitude", "longitude"]].values)
    r_rad     = min_spread_km / 6371.0
    tree      = BallTree(coords, metric="haversine")
    available = np.ones(len(scored_df), dtype=bool)
    selected  = []

    while len(selected) < n:
        remaining = np.where(available)[0]
        if len(remaining) == 0:
            break
        best = remaining[0]
        selected.append(best)
        nearby = tree.query_radius(coords[best : best + 1], r=r_rad)[0]
        available[nearby] = False

    return scored_df.iloc[selected].reset_index(drop=True)


# ---------------------------------------------------------------------------
# Main — outputs top_candidates.csv
# ---------------------------------------------------------------------------

def main():
    Path(OUTPUT_DIR).mkdir(exist_ok=True)

    print("Loading data...")
    all_df, own_df, comp_df = load_all_restaurants()
    print(f"  Total pool: {len(all_df):,} restaurants "
          f"({len(own_df)} McDonald's + {len(comp_df)} competitors)")
    for cat, grp in comp_df.groupby("category"):
        w = COMPETITOR_SOURCES[cat]["weight"]
        print(f"  {cat} (w={w}): {len(grp):,} — {grp['brand'].value_counts().to_dict()}")

    print("\nFitting HDBSCAN on demand landscape...")
    clusterer = fit_demand_hdbscan(all_df)

    print("\nAssigning ALL restaurants to demand clusters (noise → nearest centroid)...")
    cluster_stats, all_labels, centroids = compute_cluster_stats(all_df, clusterer)
    print(f"  Clusters: {len(cluster_stats)}  |  All {len(all_df)} restaurants assigned")

    print("\nCluster summary (top 10 by demand):")
    top_clusters = cluster_stats.sort_values("total_demand", ascending=False).head(10)
    print(top_clusters[["total_demand", "n_restaurants", "mcd_count", "mcd_gap"]].to_string(
        float_format="{:.2f}".format
    ))

    print("\nBuilding spatial indices...")
    own_tree  = build_balltree(own_df)
    comp_tree = build_balltree(comp_df)

    print("Generating candidate grid...")
    candidates = generate_candidate_grid()
    print(f"  Grid: {len(candidates):,} points")

    print("Scoring candidates...")
    scored = score_candidates(
        candidates, own_df, comp_df, clusterer,
        cluster_stats, centroids, own_tree, comp_tree,
    )

    print(f"Selecting top {TOP_N_SITES} with geographic diversity (min spread {MIN_SPREAD_KM} km)...")
    top = greedy_diversity_select(scored, TOP_N_SITES, MIN_SPREAD_KM)

    display_cols = [
        "latitude", "longitude", "score",
        "cluster_label", "membership_strength", "was_noise",
        "cluster_demand_score", "mcd_gap_score", "distance_buffer",
        "dist_to_own_km", "dist_to_comp_km",
        "total_demand", "mcd_count", "n_restaurants",
    ]
    print(f"\nTop {TOP_N_SITES} candidate sites:")
    print(top[display_cols].to_string(index=False, float_format="{:.3f}".format))

    top[display_cols].to_csv(OUTPUT_CSV, index=False)
    print(f"\nSaved: {OUTPUT_CSV}")
    print("Run app_interactive.py to generate the interactive map.")


if __name__ == "__main__":
    main()
