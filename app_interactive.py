"""
McDonald's Tokyo — Interactive Map

Generates a self-contained HTML map with live scoring controls:
  • Burger / Teishoku / Family demand-weight inputs — adjust how much each
    competitor category contributes to the cluster demand signal (default values
    match config_modeling.py: 1.0 / 0.5 / 0.3).
  • Sparse-area confidence slider — controls the membership weight for
    HDBSCAN noise-reassigned candidates (0 = hidden, 1 = equal weight).
  • Top-N candidates slider — show 5–50 ranked sites (default 50).

All scoring and greedy NMS run in-browser; the map updates instantly.

Output: output/interactive_map.html  (self-contained, no server required)
"""

import json
import numpy as np
import pandas as pd
import folium
import folium.plugins
from pathlib import Path

from site_selection import (
    load_all_restaurants,
    fit_demand_hdbscan,
    generate_candidate_grid,
    compute_cluster_stats,
    score_candidates,
    OWN_BRAND,
    CATEGORY_STYLE,
    NOISE_MEMBERSHIP,
)
from config_modeling import (
    TOP_N_SITES, MIN_SPREAD_KM, OUTPUT_DIR, COMPETITOR_SOURCES, BBOX, SCORE_WEIGHTS,
)
from spatial_features import build_balltree

OUTPUT_MAP = "output/interactive_map.html"

# Demand weight defaults — match COMPETITOR_SOURCES weights in config_modeling.py
DEFAULT_W_BURGER   = 1.0
DEFAULT_W_TEISHOKU = 0.5
DEFAULT_W_FAMILY   = 0.3

_CAND_COLS_V2 = [
    "latitude", "longitude", "was_noise", "base_score", "raw_membership",
    "cluster_label", "cluster_demand_score", "mcd_gap_score", "distance_buffer",
    "affordability_score", "avg_land_price",
    "dist_to_own_km", "dist_to_comp_km", "total_demand", "mcd_count", "n_restaurants",
    "burger_demand", "teishoku_demand", "family_demand", "mcd_demand_contrib",
]


# ---------------------------------------------------------------------------
# Per-category cluster demand enrichment
# ---------------------------------------------------------------------------

def _enrich_cluster_stats_categories(
    all_df: pd.DataFrame,
    all_labels: np.ndarray,
    cluster_stats: pd.DataFrame,
) -> pd.DataFrame:
    """
    Add burger_demand, teishoku_demand, family_demand, mcd_demand_contrib columns
    to cluster_stats so the browser can recompute weighted demand scores.

    burger_demand  — review sum for non-McDonald's burger chains in each cluster
    teishoku_demand — review sum for teishoku chains
    family_demand  — review sum for family restaurants
    mcd_demand_contrib — review sum for existing McDonald's (always weight=1 in JS)
    """
    df = all_df.copy()
    df["cluster"] = all_labels

    # Burger competitors only (McDonald's own stores are excluded here)
    burger_comp = df[(df["category"] == "burger") & (~df["is_own"])]
    cluster_stats["burger_demand"] = (
        burger_comp.groupby("cluster")["review_count"].sum()
        .reindex(cluster_stats.index).fillna(0).astype(int)
    )

    # Teishoku and family
    for cat in ["teishoku", "family"]:
        g = df[df["category"] == cat].groupby("cluster")["review_count"].sum()
        cluster_stats[f"{cat}_demand"] = g.reindex(cluster_stats.index).fillna(0).astype(int)

    # McDonald's own contribution (always kept at full weight in browser)
    mcd = df[df["is_own"] == True].groupby("cluster")["review_count"].sum()
    cluster_stats["mcd_demand_contrib"] = mcd.reindex(cluster_stats.index).fillna(0).astype(int)

    return cluster_stats


# ---------------------------------------------------------------------------
# JSON serialisation
# ---------------------------------------------------------------------------

def _serialise_candidates(scored: pd.DataFrame) -> str:
    data = scored[_CAND_COLS_V2].copy()
    data = data.rename(columns={
        "latitude":  "lat",
        "longitude": "lon",
        "burger_demand":      "burger_d",
        "teishoku_demand":    "teishoku_d",
        "family_demand":      "family_d",
        "mcd_demand_contrib": "mcd_d",
    })
    data["was_noise"] = data["was_noise"].astype(bool)
    for col in ["base_score", "raw_membership", "cluster_demand_score",
                "mcd_gap_score", "distance_buffer", "affordability_score",
                "dist_to_own_km", "dist_to_comp_km"]:
        data[col] = data[col].round(5)
    records = data.to_dict("records")
    for i, rec in enumerate(records):
        if "nearby" in scored.columns:
            rec["nearby"] = scored["nearby"].iat[i]
        if "nearest_own_name" in scored.columns:
            rec["nearest_own_name"] = scored["nearest_own_name"].iat[i]
    return json.dumps(records, ensure_ascii=False, separators=(",", ":"))


def _add_nearby_competitors(
    scored: pd.DataFrame,
    comp_df: pd.DataFrame,
    max_km: float = 1.0,
    top_n: int = 3,
) -> pd.DataFrame:
    from sklearn.neighbors import BallTree

    r_rad     = max_km / 6371.0
    cands_rad = np.radians(scored[["latitude", "longitude"]].values)

    cat_info = {}
    for cat, grp in comp_df.groupby("category"):
        coords = np.radians(grp[["latitude", "longitude"]].values)
        brands = grp["brand"].fillna("").values
        cat_info[cat] = {"tree": BallTree(coords, metric="haversine"), "brands": brands}

    nearby_all = []
    for i in range(len(scored)):
        pt, nearby = cands_rad[i : i + 1], []
        for cat in ["burger", "teishoku", "family"]:
            if cat not in cat_info:
                continue
            info = cat_info[cat]
            idxs, dists = info["tree"].query_radius(
                pt, r=r_rad, return_distance=True, sort_results=True
            )
            for pos, d in zip(idxs[0][:top_n], dists[0][:top_n]):
                nearby.append({
                    "c": cat,
                    "n": str(info["brands"][pos]),
                    "d": round(float(d) * 6371, 2),
                })
        nearby_all.append(nearby)

    out = scored.copy()
    out["nearby"] = nearby_all
    return out


def _add_nearest_own(scored: pd.DataFrame, own_df: pd.DataFrame) -> pd.DataFrame:
    """Attach the name of the nearest existing M outlet to each candidate."""
    from sklearn.neighbors import BallTree
    coords_own = np.radians(own_df[["latitude", "longitude"]].values)
    names_own  = own_df["name"].fillna(OWN_BRAND).values
    tree = BallTree(coords_own, metric="haversine")
    cands_rad = np.radians(scored[["latitude", "longitude"]].values)
    _, idxs = tree.query(cands_rad, k=1)
    out = scored.copy()
    out["nearest_own_name"] = names_own[idxs.flatten()]
    return out


# ---------------------------------------------------------------------------
# Slider panel HTML
# ---------------------------------------------------------------------------

def _title_html() -> str:
    return """
<style>
  body { padding-top:48px !important; box-sizing:border-box !important; }

  .dash-preview-wrap { margin-left:auto; position:relative; }

  .dash-btn {
    display:inline-block; font-size:13px; font-weight:600; color:#1565C0;
    text-decoration:none; padding:5px 12px; border:1px solid #1565C0;
    border-radius:5px; white-space:nowrap; background:transparent;
    transition:background 0.15s;
  }
  .dash-btn:hover { background:#E3F2FD; }

  .dash-preview {
    display:none;
    position:absolute; top:calc(100% + 8px); right:0;
    width:320px; height:200px;
    overflow:hidden;
    border-radius:8px;
    box-shadow:0 6px 24px rgba(0,0,0,0.18);
    border:1px solid #ddd;
    background:white;
    z-index:9999;
  }
  .dash-preview iframe {
    width:1280px; height:800px;
    transform:scale(0.25); transform-origin:top left;
    border:none; pointer-events:none;
  }
  .dash-preview-wrap:hover .dash-preview { display:block; }
</style>

<div style="
    position:fixed; top:0; left:0; right:0; height:48px; z-index:2000;
    background:white; padding:0 18px;
    box-shadow:0 2px 6px rgba(0,0,0,0.15); font-family:sans-serif;
    font-size:20px; font-weight:bold; color:#1a1a1a;
    display:flex; align-items:center;
">
  Geo-intelligence Decision System&nbsp;<span style="color:#888;font-weight:normal;font-size:16px;">(Demo)</span>

  <div class="dash-preview-wrap">
    <a href="competitor_dashboard.html" target="_blank" class="dash-btn">
      Competitor Dashboard ↗
    </a>
    <div class="dash-preview">
      <iframe src="competitor_dashboard.html" scrolling="no"></iframe>
    </div>
  </div>
</div>
"""


def _slider_panel_html() -> str:
    return f"""
<div id="slider-panel" style="
    position:fixed; bottom:20px; right:12px; z-index:1000;
    background:white; padding:14px 18px; border-radius:10px;
    box-shadow:0 3px 14px rgba(0,0,0,0.25); font-family:sans-serif;
    font-size:13px; min-width:255px; max-width:275px; line-height:1.5;
">
  <div style="font-weight:bold;margin-bottom:12px;font-size:14px;
       border-bottom:1px solid #eee;padding-bottom:8px;">
    🎛&nbsp; Display Controls
  </div>

  <!-- Sparse area confidence -->
  <div style="margin-bottom:10px;">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:2px;">
      <span>🟠&nbsp;Sparse Area Confidence</span>
      <span id="noise-val" style="font-weight:bold;color:#E65100;font-size:13px;">0.50</span>
    </div>
    <input type="range" id="noise-slider" min="0" max="1" step="0.05" value="0.50"
           style="width:100%;accent-color:#E65100;cursor:pointer;">
    <div style="display:flex;justify-content:space-between;font-size:10px;color:#aaa;">
      <span>0 — hidden</span><span>1 — equal weight</span>
    </div>
  </div>

  <div style="border-top:1px solid #eee;margin:10px 0;"></div>

  <!-- Top N -->
  <div style="margin-bottom:6px;">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:2px;">
      <span>📊&nbsp;Top Candidates Shown</span>
      <span id="topn-val" style="font-weight:bold;color:#1565C0;font-size:13px;">{TOP_N_SITES}</span>
    </div>
    <input type="range" id="topn-slider" min="5" max="50" step="1" value="{TOP_N_SITES}"
           style="width:100%;accent-color:#1565C0;cursor:pointer;">
    <div style="display:flex;justify-content:space-between;font-size:10px;color:#aaa;">
      <span>5</span><span>50</span>
    </div>
  </div>

  <!-- Stats -->
  <div id="slider-stats" style="font-size:11px;color:#444;
       border-top:1px solid #eee;padding-top:8px;margin:8px 0;line-height:1.8;"></div>

  <!-- Legend -->
  <div style="font-size:11px;color:#666;border-top:1px solid #eee;padding-top:8px;line-height:1.9;">
    <span style="color:#1B5E20;font-size:15px;">●</span>&nbsp;Confirmed demand cluster<br>
    <span style="color:#E65100;font-size:15px;">●</span>&nbsp;Sparse / latent-demand area<br>
    <span style="background:#DA291C;color:#FFC72C;font-weight:900;font-size:11px;
      border-radius:3px;padding:0 3px;">M</span>&nbsp;Existing McDonald's<br>
    <span style="color:#aaa;font-size:10px;">Numbers = rank &nbsp;·&nbsp; Opacity = score</span>
  </div>
</div>
"""


# ---------------------------------------------------------------------------
# JavaScript
# ---------------------------------------------------------------------------

def _js_code(map_name: str, cands_json: str, min_spread_km: float) -> str:
    sw_demand = SCORE_WEIGHTS["cluster_demand"]
    sw_gap    = SCORE_WEIGHTS["mcd_gap"]
    sw_buffer = SCORE_WEIGHTS["distance_buffer"]
    return f"""
document.addEventListener('DOMContentLoaded', function() {{
(function() {{
  var CANDS     = {cands_json};
  var MIN_KM    = {min_spread_km};
  var lmap      = {map_name};
  var SW_DEMAND = {sw_demand};
  var SW_GAP    = {sw_gap};
  var SW_BUFFER = {sw_buffer};

  var candLayer = L.layerGroup().addTo(lmap);

  // ---------- helpers ----------

  function hvKm(lat1, lon1, lat2, lon2) {{
    var R = 6371, d2r = Math.PI / 180;
    var dLat = (lat2 - lat1) * d2r, dLon = (lon2 - lon1) * d2r;
    var a = Math.sin(dLat/2)*Math.sin(dLat/2) +
            Math.cos(lat1*d2r)*Math.cos(lat2*d2r)*Math.sin(dLon/2)*Math.sin(dLon/2);
    return 2 * R * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  }}

  function greedyNMS(sorted, n, minKm) {{
    var sel = [], skip = new Uint8Array(sorted.length);
    for (var i = 0; i < sorted.length && sel.length < n; i++) {{
      if (skip[i]) continue;
      var c = Object.assign({{rank: sel.length + 1}}, sorted[i]);
      sel.push(c);
      for (var j = i+1; j < sorted.length; j++) {{
        if (!skip[j] && hvKm(c.lat, c.lon, sorted[j].lat, sorted[j].lon) < minKm)
          skip[j] = 1;
      }}
    }}
    return sel;
  }}

  var CAT_COLOR = {{burger:'E65100', teishoku:'6A1B9A', family:'00695C'}};
  var CAT_LABEL = {{burger:'Burger', teishoku:'Teishoku', family:'Family'}};

  function nearbyHtml(nearby) {{
    if (!nearby || nearby.length === 0)
      return '<div style="margin-top:5px;font-size:10px;color:#aaa;">No competitors within 1 km</div>';
    var groups = {{}};
    nearby.forEach(function(n) {{
      if (!groups[n.c]) groups[n.c] = [];
      groups[n.c].push(n);
    }});
    var html = '<div style="margin-top:6px;border-top:1px solid #ddd;padding-top:5px;font-size:11px;">' +
               '<b>Nearby competitors (≤ 1 km)</b><br>';
    ['burger','teishoku','family'].forEach(function(cat) {{
      if (!groups[cat]) return;
      var col = CAT_COLOR[cat], lbl = CAT_LABEL[cat];
      var parts = groups[cat].map(function(n) {{
        var dist = n.d < 1 ? Math.round(n.d*1000)+' m' : n.d.toFixed(1)+' km';
        return '<span style="color:#333">'+n.n+'</span>'+
               '&nbsp;<span style="color:#999;font-size:10px;">('+dist+')</span>';
      }});
      html += '<span style="color:#'+col+'">●</span>&nbsp;<b>'+lbl+':</b>&nbsp;'+
              parts.join('&nbsp;&nbsp;')+'<br>';
    }});
    return html+'</div>';
  }}

  function badge(rank, noise, op) {{
    var bg = noise ? '#E65100' : '#1B5E20', bd = noise ? '#FF8A65' : '#66BB6A';
    return '<div style="background:'+bg+';color:#fff;border:2.5px solid '+bd+';'+
      'border-radius:50%;width:26px;height:26px;display:flex;align-items:center;'+
      'justify-content:center;font-weight:bold;font-size:11px;'+
      'box-shadow:0 2px 5px rgba(0,0,0,.4);opacity:'+op.toFixed(2)+';'+
      'font-family:sans-serif;">'+rank+'</div>';
  }}

  // ---------- core update ----------

  function getWeight(id, fallback) {{
    var el = document.getElementById(id);
    if (!el) return fallback;
    var v = parseFloat(el.value);
    return isNaN(v) || v < 0 ? fallback : v;
  }}

  function updateMap() {{
    var wB   = getWeight('burger-weight',   {DEFAULT_W_BURGER});
    var wT   = getWeight('teishoku-weight', {DEFAULT_W_TEISHOKU});
    var wF   = getWeight('family-weight',   {DEFAULT_W_FAMILY});
    var nm   = parseFloat(document.getElementById('noise-slider').value);
    var topN = parseInt(document.getElementById('topn-slider').value, 10);

    document.getElementById('noise-val').textContent = nm.toFixed(2);
    document.getElementById('topn-val').textContent  = topN;

    // Step 1 — weighted demand per candidate
    var maxWD = 0;
    var sc = CANDS.map(function(c) {{
      var mem = c.was_noise ? nm : c.raw_membership;
      var wd  = wB * c.burger_d + wT * c.teishoku_d + wF * c.family_d + c.mcd_d;
      if (wd > maxWD) maxWD = wd;
      return Object.assign({{_mem: mem, _wd: wd}}, c);
    }});
    if (maxWD === 0) maxWD = 1;

    // Step 2 — recompute base_score with new demand signal
    var maxRaw = 0;
    sc.forEach(function(c) {{
      var demandScore = c._wd / maxWD;
      var base = SW_DEMAND * demandScore + SW_GAP * c.mcd_gap_score + SW_BUFFER * c.distance_buffer;
      c._raw = base * c._mem;
      if (c._raw > maxRaw) maxRaw = c._raw;
    }});
    if (maxRaw === 0) maxRaw = 1;

    // Step 3 — normalise + sort
    sc.forEach(function(c) {{ c.score = c._raw / maxRaw; }});
    sc.sort(function(a, b) {{ return b.score - a.score; }});

    // Step 4 — greedy NMS with user-selected topN
    var top = greedyNMS(sc, topN, MIN_KM);

    // Step 5 — render markers
    candLayer.clearLayers();
    var nC = 0, nS = 0;
    top.forEach(function(c) {{
      var op  = 0.45 + 0.50 * c.score;
      var ico = L.divIcon({{
        html: badge(c.rank, c.was_noise, op),
        iconSize: [26,26], iconAnchor: [13,13], className:''
      }});
      var wDem = Math.round(wB*c.burger_d + wT*c.teishoku_d + wF*c.family_d + c.mcd_d);
      var pop =
        '<b>Rank #'+c.rank+'</b>'+
        (c.was_noise ? ' <span style="color:#E65100">[sparse area]</span>' : '')+'<br>'+
        'Score: '+c.score.toFixed(3)+'<br>'+
        'Cluster #'+c.cluster_label+' ('+c.n_restaurants+
          ' restaurants, '+c.total_demand+' total reviews)<br>'+
        'Weighted demand: '+wDem+
          ' <span style="font-size:10px;color:#888;">' +
          '(🟠'+c.burger_d+' 🟣'+c.teishoku_d+' 🟢'+c.family_d+' M'+c.mcd_d+')</span><br>'+
        "McDonald's in cluster: "+c.mcd_count+
          ' ('+(c.mcd_gap_score*100).toFixed(0)+'% gap)<br>'+
        'Membership: '+c._mem.toFixed(2)+'<br>'+
        "Dist to nearest M: "+c.dist_to_own_km.toFixed(2)+' km'+
        (c.nearest_own_name ? ' ('+c.nearest_own_name+')' : '')+
        nearbyHtml(c.nearby)+
        '<div style="margin-top:5px;border-top:1px solid #ddd;padding-top:5px;font-size:11px;">'+
        '💴 Land price: ¥'+(c.avg_land_price/10000).toFixed(0)+'万/m²'+
        ' <span style="color:#888;">(affordability='+c.affordability_score.toFixed(2)+')</span>'+
        '</div>';
      L.marker([c.lat, c.lon], {{icon: ico}})
       .bindPopup(pop, {{maxWidth: 340}})
       .bindTooltip('#'+c.rank+(c.was_noise?' (sparse) ':' ')+'score='+c.score.toFixed(3))
       .addTo(candLayer);
      if (c.was_noise) nS++; else nC++;
    }});

    var el = document.getElementById('slider-stats');
    if (el) el.innerHTML =
      'Showing <b>'+top.length+'</b> sites&nbsp;|&nbsp;'+
      '<span style="color:#1B5E20">●</span> '+nC+' confirmed&nbsp;&nbsp;'+
      '<span style="color:#E65100">●</span> '+nS+' sparse';
  }}

  // ---------- wire up controls ----------
  // text inputs in the layer control + sliders in the side panel
  ['burger-weight','teishoku-weight','family-weight','noise-slider','topn-slider']
    .forEach(function(id) {{
      var el = document.getElementById(id);
      if (el) el.addEventListener('input', updateMap);
    }});

  updateMap();
}})();
}});
"""


# ---------------------------------------------------------------------------
# Map builder
# ---------------------------------------------------------------------------

def build_map(
    scored:  pd.DataFrame,
    own_df:  pd.DataFrame,
    comp_df: pd.DataFrame,
    all_df:  pd.DataFrame,
) -> folium.Map:
    center_lat = (BBOX["lat_min"] + BBOX["lat_max"]) / 2
    center_lon = (BBOX["lon_min"] + BBOX["lon_max"]) / 2
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=12,
        tiles=None,
        control_scale=True,
    )
    folium.TileLayer("CartoDB Positron", name="CartoBaseMap").add_to(m)
    folium.TileLayer("OpenStreetMap", name="OpenStreetMap").add_to(m)

    # Study area bounding box
    folium.Rectangle(
        bounds=[
            [BBOX["lat_min"], BBOX["lon_min"]],
            [BBOX["lat_max"], BBOX["lon_max"]],
        ],
        color="#1565C0",
        weight=2,
        dash_array="8 5",
        fill=False,
        tooltip="Study area (Tokyo 23 wards + surrounds)",
    ).add_to(m)

    # Demand heatmap
    heat = all_df[all_df["review_count"] > 0]
    folium.plugins.HeatMap(
        heat[["latitude", "longitude", "review_count"]].values.tolist(),
        name="Demand heatmap (review-weighted)",
        min_opacity=0.25, radius=18, blur=22, max_zoom=14, show=True,
    ).add_to(m)

    # Existing McDonald's — red badge with yellow M
    mcd_icon_html = (
        '<div style="background:#DA291C;color:#FFC72C;border:2px solid #b01e14;'
        'border-radius:6px;width:22px;height:22px;display:flex;align-items:center;'
        'justify-content:center;font-weight:900;font-size:15px;font-family:Arial,sans-serif;'
        'box-shadow:0 2px 5px rgba(0,0,0,0.45);line-height:1;">M</div>'
    )
    own_grp = folium.FeatureGroup(
        name='<span style="background:#DA291C;color:#FFC72C;font-weight:900;'
             'font-size:11px;border-radius:3px;padding:1px 4px;">M</span>'
             "&nbsp; McDonald's (existing)",
        show=True,
    )
    for _, row in own_df.iterrows():
        folium.Marker(
            [row["latitude"], row["longitude"]],
            icon=folium.DivIcon(html=mcd_icon_html, icon_size=(22, 22), icon_anchor=(11, 11)),
            popup=folium.Popup(
                f"<b>{row.get('name', OWN_BRAND)}</b><br>Reviews: {int(row['review_count'])}",
                max_width=220,
            ),
            tooltip=row.get("name", OWN_BRAND),
        ).add_to(own_grp)
    own_grp.add_to(m)

    # Competitor layers (hidden by default)
    # Each layer label embeds a text input for the demand weight used in scoring.
    _cat_weight_defaults = {
        "burger":   DEFAULT_W_BURGER,
        "teishoku": DEFAULT_W_TEISHOKU,
        "family":   DEFAULT_W_FAMILY,
    }
    for cat, style in CATEGORY_STYLE.items():
        subset = comp_df[comp_df["category"] == cat]
        if subset.empty:
            continue
        w_default = _cat_weight_defaults[cat]
        weight_input = (
            f'<input type="text" id="{cat}-weight" value="{w_default}"'
            f' style="width:36px;font-size:11px;padding:1px 4px;'
            f'border:1px solid #bbb;border-radius:3px;text-align:center;'
            f'vertical-align:middle;margin-left:4px;background:#fafafa;"'
            f' title="Demand weight for {cat} chains"'
            f' onclick="event.stopPropagation()"'
            f' onkeydown="event.stopPropagation()">'
        )
        grp = folium.FeatureGroup(
            name=(
                f'<span style="color:{style["colour"]};font-size:14px;">⬤</span>'
                f"&nbsp;{style['label']}&nbsp;{weight_input}"
            ),
            show=False,
        )
        for _, row in subset.iterrows():
            folium.CircleMarker(
                [row["latitude"], row["longitude"]],
                radius=style["radius"] - 1, color=style["colour"], weight=1,
                fill=True, fill_color=style["colour"],
                fill_opacity=style["opacity"] - 0.1,
                tooltip=f"{row.get('name','')} ({row['brand']}) — {int(row['review_count'])} reviews",
            ).add_to(grp)
        grp.add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)

    # Inject title, slider panel + JS
    cands_json = _serialise_candidates(scored)
    m.get_root().html.add_child(folium.Element(_title_html()))
    m.get_root().html.add_child(folium.Element(_slider_panel_html()))
    m.get_root().script.add_child(
        folium.Element(_js_code(m.get_name(), cands_json, MIN_SPREAD_KM))
    )
    return m


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    Path(OUTPUT_DIR).mkdir(exist_ok=True)

    print("Loading data...")
    all_df, own_df, comp_df = load_all_restaurants()
    print(f"  Total pool: {len(all_df):,} restaurants "
          f"({len(own_df)} McDonald's + {len(comp_df)} competitors)")

    print("\nFitting HDBSCAN...")
    clusterer = fit_demand_hdbscan(all_df)

    print("\nAssigning ALL restaurants to demand clusters (noise → nearest centroid)...")
    cluster_stats, all_labels, centroids = compute_cluster_stats(all_df, clusterer)
    print(f"  Clusters: {len(cluster_stats)}")

    print("Enriching cluster stats with per-category demand...")
    cluster_stats = _enrich_cluster_stats_categories(all_df, all_labels, cluster_stats)

    print("\nBuilding spatial indices...")
    own_tree  = build_balltree(own_df)
    comp_tree = build_balltree(comp_df)

    print("Generating candidate grid...")
    candidates = generate_candidate_grid()
    print(f"  Grid: {len(candidates):,} points")

    print("Scoring ALL candidates (full pool — NMS runs in browser)...")
    scored = score_candidates(
        candidates, own_df, comp_df, clusterer,
        cluster_stats, centroids, own_tree, comp_tree,
    )

    # Join per-category demand columns onto scored candidates
    scored = scored.join(
        cluster_stats[["burger_demand", "teishoku_demand", "family_demand", "mcd_demand_contrib"]],
        on="cluster_label",
    )
    for col in ["burger_demand", "teishoku_demand", "family_demand", "mcd_demand_contrib"]:
        scored[col] = scored[col].fillna(0).astype(int)

    # Ensure affordability columns are present (computed in score_candidates)
    for col in ["affordability_score", "avg_land_price"]:
        if col not in scored.columns:
            scored[col] = 0.0

    n_noise = int(scored["was_noise"].sum())
    print(f"  Filtered pool: {len(scored):,} candidates "
          f"({n_noise} sparse/noise-reassigned, {len(scored)-n_noise} confirmed)")

    print("Finding nearby competitors for each candidate (≤ 1 km, top 3 per category)...")
    scored = _add_nearby_competitors(scored, comp_df)
    scored = _add_nearest_own(scored, own_df)

    print("\nBuilding interactive map with category weight sliders...")
    m = build_map(scored, own_df, comp_df, all_df)
    m.save(OUTPUT_MAP)
    print(f"Saved: {OUTPUT_MAP}")
    print("\nOpen in a browser — use the right-side panel to adjust:")
    print("  • Burger / Teishoku / Family demand weights (0 = ignore, 2 = double influence)")
    print("  • Sparse area confidence (noise membership)")
    print("  • Top N candidates shown (5–50)")


if __name__ == "__main__":
    main()
