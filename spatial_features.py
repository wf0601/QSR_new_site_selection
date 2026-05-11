# =============================================================================
# spatial_features.py — Fast vectorised spatial aggregation
# =============================================================================

import numpy as np
import pandas as pd
from sklearn.neighbors import BallTree
from config_modeling import RADII_KM

EARTH_RADIUS_KM = 6371.0


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_balltree(df: pd.DataFrame) -> BallTree:
    """Build a haversine BallTree from a dataframe with lat/lon columns."""
    coords_rad = np.radians(df[["latitude", "longitude"]].values)
    return BallTree(coords_rad, metric="haversine", leaf_size=40)


def compute_spatial_features(
    source_df: pd.DataFrame,
    target_df: pd.DataFrame,
    prefix: str,
    radii_km: list = None,
    source_tree: BallTree = None,
) -> pd.DataFrame:
    """
    For each row in target_df compute aggregated features from source_df
    at every radius in radii_km.

    Returns a DataFrame (same index as target_df) with columns:
        {prefix}_count_{r}km
        {prefix}_pop_sum_{r}km
        {prefix}_pop_max_{r}km

    Strategy: query at max radius once per target point, then filter
    sub-arrays in numpy — avoids rebuilding trees per point.
    """
    if radii_km is None:
        radii_km = RADII_KM

    src_coords = np.radians(source_df[["latitude", "longitude"]].values)
    tgt_coords = np.radians(target_df[["latitude", "longitude"]].values)
    pop        = source_df["popularity"].values

    if source_tree is None:
        source_tree = BallTree(src_coords, metric="haversine", leaf_size=40)

    max_r_rad = max(radii_km) / EARTH_RADIUS_KM

    # Single query at maximum radius — O(N log N) total
    all_idx, all_dist = source_tree.query_radius(
        tgt_coords, r=max_r_rad, return_distance=True
    )

    results = {}
    for r in radii_km:
        r_rad   = r / EARTH_RADIUS_KM
        counts  = np.zeros(len(target_df), dtype=int)
        pop_sum = np.zeros(len(target_df), dtype=float)
        pop_max = np.zeros(len(target_df), dtype=float)

        for i, (idx, dist) in enumerate(zip(all_idx, all_dist)):
            if len(idx) == 0:
                continue
            mask       = dist <= r_rad
            valid_idx  = idx[mask]
            if len(valid_idx) == 0:
                continue
            counts[i]  = len(valid_idx)
            pop_sub    = pop[valid_idx]
            pop_sum[i] = pop_sub.sum()
            pop_max[i] = pop_sub.max()

        results[f"{prefix}_count_{r}km"]   = counts
        results[f"{prefix}_pop_sum_{r}km"] = pop_sum
        results[f"{prefix}_pop_max_{r}km"] = pop_max

    return pd.DataFrame(results, index=target_df.index)


def add_nearest_distance(
    target_df: pd.DataFrame,
    source_df: pd.DataFrame,
    col_name: str,
    source_tree: BallTree = None,
) -> pd.Series:
    """
    Returns a Series (km) of distance from each target point to its
    nearest source point.
    """
    if source_tree is None:
        source_tree = build_balltree(source_df)

    tgt_coords = np.radians(target_df[["latitude", "longitude"]].values)
    dist_rad, _ = source_tree.query(tgt_coords, k=1)
    return pd.Series(
        dist_rad.flatten() * EARTH_RADIUS_KM,
        index=target_df.index,
        name=col_name,
    )


def build_feature_matrix(own_df: pd.DataFrame, comp_df: pd.DataFrame) -> pd.DataFrame:
    """
    Build the full feature matrix for own restaurants (used to fit HDBSCAN).
    """
    comp_tree = build_balltree(comp_df)
    own_tree  = build_balltree(own_df)

    print("[features] Computing competitor features for own sites...")
    comp_feats = compute_spatial_features(
        comp_df, own_df, prefix="comp", source_tree=comp_tree
    )

    print("[features] Computing self-distance (nearest own neighbour)...")
    own_df["dist_to_nearest_own_km"] = add_nearest_distance(
        own_df, own_df, col_name="dist_to_nearest_own_km", source_tree=own_tree
    )

    feature_df = pd.concat([own_df[["latitude", "longitude", "popularity"]], comp_feats], axis=1)
    print(f"[features] Feature matrix: {feature_df.shape}")
    return feature_df, comp_tree, own_tree