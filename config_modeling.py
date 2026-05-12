# =============================================================================
# config_modeling.py — All tunable parameters in one place
# =============================================================================

# ---------------------------------------------------------------------------
# Study area bounding box  (Tokyo 23 wards + surrounds)
# ---------------------------------------------------------------------------
CITY_CENTER_LAT = 35.68
CITY_CENTER_LON = 139.76

BBOX = {
    "lat_min": 35.55,
    "lat_max": 35.80,
    "lon_min": 139.60,
    "lon_max": 139.90,
}

# ---------------------------------------------------------------------------
# Data paths
# ---------------------------------------------------------------------------
OWN_RESTAURANTS_CSV = "data/mcdonalds_tokyo.csv"

# Competitor tiers with relative weights.
# weight is used only when computing weighted competitive pressure for the
# distance-buffer filter.  HDBSCAN demand clustering uses raw review_count
# so that all restaurant types contribute equally to demand signal.
COMPETITOR_SOURCES = {
    "burger": {
        "path": "data/tokyo_burger_chains.csv",
        "weight": 1.0,          # direct competitors — same product
        "exclude_brand": "マクドナルド",
    },
    "teishoku": {
        "path": "data/tokyo_teishoku_chains.csv",
        "weight": 0.5,          # indirect — fast-casual, overlapping customer base
    },
    "family": {
        "path": "data/tokyo_family_chains.csv",
        "weight": 0.3,          # indirect — sit-down family dining
    },
}

# ---------------------------------------------------------------------------
# Spatial feature radii — kept for spatial_features.py compatibility
# ---------------------------------------------------------------------------
RADII_KM = [0.5, 1.0, 2.0]

# ---------------------------------------------------------------------------
# HDBSCAN parameters
# Fits on ALL restaurants (lat/lon in radians) weighted by review_count.
# haversine metric gives proper spherical distances.
# ---------------------------------------------------------------------------
HDBSCAN_PARAMS = {
    "min_cluster_size"        : 5,    # minimum restaurants to form a demand cluster
    "min_samples"             : 2,
    "metric"                  : "haversine",
    "prediction_data"         : True,
    "core_dist_n_jobs"        : -1,
    "cluster_selection_method": "eom",
}

# ---------------------------------------------------------------------------
# Candidate grid
# ---------------------------------------------------------------------------
GRID_STEP_DEG = 0.003   # ~330 m spacing → ~8,500 points across Tokyo bbox

# ---------------------------------------------------------------------------
# Candidate filtering thresholds
# ---------------------------------------------------------------------------
MIN_DIST_TO_OWN_KM      = 0.8    # cannibalization guard
MAX_DIST_TO_COMP_KM     = 3.0    # must be near some market activity
MIN_MEMBERSHIP_STRENGTH = 0.1    # minimum soft-cluster confidence to keep a candidate

# ---------------------------------------------------------------------------
# Scoring weights (must sum to 1.0)
#   cluster_demand  — how much total review-weighted demand is in the cluster
#   mcd_gap         — how underrepresented McDonald's is in that cluster
#   distance_buffer — safe spacing from existing stores
# Final score is multiplied by membership_strength (confidence gate).
# ---------------------------------------------------------------------------
SCORE_WEIGHTS = {
    "cluster_demand" : 0.40,
    "mcd_gap"        : 0.40,
    "distance_buffer": 0.20,
}

# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------
TOP_N_SITES    = 50
MIN_SPREAD_KM  = 1.5   # minimum distance between any two selected candidate sites
OUTPUT_DIR   = "output"
OUTPUT_MAP   = "output/interactive_map.html"
OUTPUT_CSV   = "output/top_candidates.csv"
