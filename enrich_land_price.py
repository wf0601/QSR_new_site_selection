"""
Land price enrichment for restaurant data.

Reads apartment sale listings from real_estate_data/*.csv, computes an
average price-per-sqm at the town level (one below ward), and attaches
that figure to every restaurant row.  Falls back to the ward average when
no town-level listings exist.

Outputs
-------
data/land_price_lookup.csv   — town + ward averages (reference table)
data/restaurants_with_land_price.csv — all restaurants + land_price_per_sqm
"""

import re
import glob
import pandas as pd
import numpy as np
from pathlib import Path

RE_DATA_DIR  = "real_estate_data"
OUTPUT_DIR   = "data"
LOOKUP_CSV   = f"{OUTPUT_DIR}/land_price_lookup.csv"
ENRICHED_CSV = f"{OUTPUT_DIR}/restaurants_with_land_price.csv"


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def _parse_price(s) -> float | None:
    """'1680万円', '1億2000万円' → yen as float."""
    if not isinstance(s, str):
        return None
    s = s.replace(",", "").replace("，", "")
    oku = re.search(r"(\d+\.?\d*)億", s)
    man = re.search(r"(\d+\.?\d*)万", s)
    price = 0.0
    if oku:
        price += float(oku.group(1)) * 1e8
    if man:
        price += float(man.group(1)) * 1e4
    return price if price > 0 else None


def _parse_area(s) -> float | None:
    """'29.16m2（壁芯）' → 29.16."""
    if not isinstance(s, str):
        return None
    m = re.search(r"(\d+\.?\d*)m2", s)
    return float(m.group(1)) if m else None


def _extract_ward_town(addr: str) -> tuple[str | None, str | None]:
    """
    '東京都新宿区北新宿４-33-3' → ('新宿区', '北新宿')
    Strips 東京都, matches up to the FIRST 区 (avoids malformed duplicated
    addresses), then takes every character before the first digit as town.
    """
    if not isinstance(addr, str):
        return None, None
    addr = addr.replace("東京都", "")
    # [^区]+ stops at the first 区, so malformed strings like
    # '港区白金４東京都港区...' correctly yield '港区'
    m = re.match(r"([^区]+区)(.*)", addr)
    if not m:
        return None, None
    ward = m.group(1)
    rest = m.group(2).strip()
    town_m = re.match(r"([^\d１２３４５６７８９０]+)", rest)
    town = town_m.group(1).strip() if town_m else None
    return ward, town


# ---------------------------------------------------------------------------
# Build land price lookup from real estate CSVs
# ---------------------------------------------------------------------------

def _iqr_cap(series: pd.Series) -> pd.Series:
    """Remove values above Q3 + 1.5 × IQR (high-end outliers only)."""
    q1, q3 = series.quantile(0.25), series.quantile(0.75)
    upper = q3 + 1.5 * (q3 - q1)
    return series[series <= upper]


def build_land_price_lookup() -> pd.DataFrame:
    frames = []
    for path in glob.glob(f"{RE_DATA_DIR}/*.csv"):
        df = pd.read_csv(path)
        df["_price"] = df["販売価格"].apply(_parse_price)
        df["_area"]  = df["専有面積"].apply(_parse_area)
        df = df.dropna(subset=["_price", "_area", "所在地"])
        df["_ppsm"] = df["_price"] / df["_area"]
        df[["_ward", "_town"]] = df["所在地"].apply(
            lambda a: pd.Series(_extract_ward_town(a))
        )
        frames.append(df[["_ward", "_town", "_ppsm"]])

    listings = pd.concat(frames, ignore_index=True)
    listings = listings.dropna(subset=["_ward", "_town"])

    # Ward-level IQR cap — compute the upper fence per ward, then filter
    ward_upper = (
        listings.groupby("_ward")["_ppsm"]
        .apply(lambda s: s.quantile(0.75) + 1.5 * (s.quantile(0.75) - s.quantile(0.25)))
        .rename("_upper")
    )
    listings = listings.join(ward_upper, on="_ward")
    n_before = len(listings)
    listings = listings[listings["_ppsm"] <= listings["_upper"]].drop(columns="_upper")
    n_removed = n_before - len(listings)

    print(f"  Outlier removal (IQR per ward): removed {n_removed} / {n_before} listings "
          f"({100*n_removed/n_before:.1f}%)")

    # Town-level average (on IQR-cleaned data)
    town_avg = (
        listings.groupby(["_ward", "_town"])["_ppsm"]
        .agg(avg_price_per_sqm="mean", n_listings="count")
        .reset_index()
        .rename(columns={"_ward": "ward", "_town": "town"})
    )
    town_avg["source"] = "town"

    # Ward-level fallback average (also on IQR-cleaned data)
    ward_avg = (
        listings.groupby("_ward")["_ppsm"]
        .agg(avg_price_per_sqm="mean", n_listings="count")
        .reset_index()
        .rename(columns={"_ward": "ward"})
    )
    ward_avg["town"]   = None
    ward_avg["source"] = "ward_fallback"

    lookup = pd.concat([town_avg, ward_avg], ignore_index=True)
    lookup["avg_price_per_sqm"] = lookup["avg_price_per_sqm"].round(0).astype(int)
    return lookup


# ---------------------------------------------------------------------------
# Attach land price to a restaurant DataFrame
# ---------------------------------------------------------------------------

def add_land_price(
    df: pd.DataFrame,
    lookup: pd.DataFrame,
) -> pd.DataFrame:
    """
    Adds columns:
      land_price_per_sqm  — average yen/m2 for the restaurant's town (or ward)
      land_price_source   — 'town' or 'ward_fallback'
    """
    town_map = (
        lookup[lookup["source"] == "town"]
        .set_index(["ward", "town"])["avg_price_per_sqm"]
        .to_dict()
    )
    ward_map = (
        lookup[lookup["source"] == "ward_fallback"]
        .set_index("ward")["avg_price_per_sqm"]
        .to_dict()
    )

    prices, sources = [], []
    for addr in df["address"]:
        ward, town = _extract_ward_town(addr)
        if ward and town and (ward, town) in town_map:
            prices.append(town_map[(ward, town)])
            sources.append("town")
        elif ward and ward in ward_map:
            prices.append(ward_map[ward])
            sources.append("ward_fallback")
        else:
            prices.append(None)
            sources.append(None)

    out = df.copy()
    out["land_price_per_sqm"] = prices
    out["land_price_source"]  = sources
    return out


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    Path(OUTPUT_DIR).mkdir(exist_ok=True)

    print("Building land price lookup from real estate listings...")
    lookup = build_land_price_lookup()

    n_towns = int((lookup["source"] == "town").sum())
    n_wards = int((lookup["source"] == "ward_fallback").sum())
    total_listings = lookup[lookup["source"] == "town"]["n_listings"].sum()
    print(f"  {total_listings:,} listings → {n_towns} town averages across {n_wards} wards")

    lookup.to_csv(LOOKUP_CSV, index=False)
    print(f"  Saved: {LOOKUP_CSV}")

    # Load all restaurants
    from site_selection import load_all_restaurants
    print("\nLoading restaurant data...")
    all_df, _, _ = load_all_restaurants()
    print(f"  {len(all_df):,} restaurants")

    # Enrich
    print("Matching land prices...")
    enriched = add_land_price(all_df, lookup)

    town_hits  = (enriched["land_price_source"] == "town").sum()
    ward_hits  = (enriched["land_price_source"] == "ward_fallback").sum()
    misses     = enriched["land_price_source"].isna().sum()
    total      = len(enriched)

    print(f"  Town-level match : {town_hits:,} / {total:,}  ({100*town_hits/total:.1f}%)")
    print(f"  Ward fallback    : {ward_hits:,} / {total:,}  ({100*ward_hits/total:.1f}%)")
    print(f"  No match         : {misses:,}  / {total:,}  ({100*misses/total:.1f}%)")

    if misses > 0:
        print(f"\n  Unmatched address samples:")
        for a in enriched[enriched["land_price_source"].isna()]["address"].dropna().head(5):
            print(f"    {a}")

    # Price summary by ward
    print("\nAverage land price by ward (yen/m²):")
    ward_summary = (
        enriched.dropna(subset=["land_price_per_sqm"])
        .groupby("ward")["land_price_per_sqm"]
        .mean()
        .sort_values(ascending=False)
        .reset_index()
    )
    ward_summary["land_price_per_sqm"] = ward_summary["land_price_per_sqm"].round(0).astype(int)
    print(ward_summary.to_string(index=False))

    cols = [c for c in enriched.columns if c not in ["land_price_per_sqm", "land_price_source"]]
    out_cols = cols + ["land_price_per_sqm", "land_price_source"]
    enriched[out_cols].to_csv(ENRICHED_CSV, index=False)
    print(f"\nSaved: {ENRICHED_CSV}")


if __name__ == "__main__":
    main()
