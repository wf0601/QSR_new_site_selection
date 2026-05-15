"""
dashboard.py — Competitor Landscape Dashboard
Generates output/competitor_dashboard.html — open in any browser, no server required.
Requires internet for Chart.js CDN.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from config_modeling import OUTPUT_DIR
from site_selection import load_all_restaurants

OUTPUT_DASHBOARD = f"{OUTPUT_DIR}/competitor_dashboard.html"

CATEGORY_COLOR = {
    "own":      "#FFC72C",   # McDonald's
    "burger":   "#E65100",   # direct burger competitors
    "teishoku": "#7B1FA2",   # teishoku chains
    "family":   "#00695C",   # family restaurants
}


def _cat_color(brand: str, brand_cat: dict[str, str]) -> str:
    return CATEGORY_COLOR.get(brand_cat.get(brand, ""), "#90A4AE")


def _ward_label(w: str) -> str:
    """chiyoda-ku → Chiyoda-ku"""
    return "-".join(p.capitalize() for p in w.split("-"))


def _j(obj) -> str:
    return json.dumps(obj, ensure_ascii=False)


def build_data(all_df: pd.DataFrame, own_df: pd.DataFrame, comp_df: pd.DataFrame) -> dict:
    # brand → category key (own / burger / teishoku / family)
    brand_cat = {
        row["brand"]: ("own" if row["is_own"] else row["category"])
        for _, row in all_df.drop_duplicates("brand").iterrows()
    }

    # ── KPIs ────────────────────────────────────────────────────────
    kpis = {
        "total":         len(all_df),
        "n_own":         len(own_df),
        "n_brands":      int(comp_df["brand"].nunique()),
        "total_reviews": int(all_df["review_count"].sum()),
    }

    # ── Brand location count (horiz bar) ────────────────────────────
    bc = (
        all_df.groupby("brand")
        .size()
        .sort_values(ascending=True)
        .reset_index(name="count")
    )
    brand_count = {
        "labels": bc["brand"].tolist(),
        "values": bc["count"].tolist(),
        "colors": [_cat_color(b, brand_cat) for b in bc["brand"]],
    }

    # ── Top 10 McDonald's by review count ───────────────────────────
    top_mcd = (
        own_df[own_df["review_count"] > 0]
        .nlargest(10, "review_count")[["name", "review_count"]]
        .iloc[::-1]  # ascending so longest bar is at top
    )
    # Strip brand prefix for cleaner labels: "マクドナルド 新宿東口店" → "新宿東口店"
    top_mcd_labels = (
        top_mcd["name"]
        .str.replace(r"^マクドナルド\s*", "", regex=True)
        .str.strip()
        .tolist()
    )
    top_mcd_outlets = {
        "labels": top_mcd_labels,
        "values": top_mcd["review_count"].tolist(),
    }

    # ── Avg reviews by brand (bar) ───────────────────────────────────
    br = (
        all_df.groupby("brand")["review_count"]
        .mean()
        .round(1)
        .sort_values(ascending=False)
        .reset_index()
    )
    brand_reviews = {
        "labels": br["brand"].tolist(),
        "values": br["review_count"].tolist(),
        "colors": [_cat_color(b, brand_cat) for b in br["brand"]],
    }

    # ── Ward competition stacked bar (top 15 wards) ──────────────────
    ward_total = (
        all_df[all_df["ward"] != ""]
        .groupby("ward")
        .size()
        .sort_values(ascending=False)
        .head(15)
    )
    mcd_per_ward = (
        own_df[own_df["ward"] != ""]
        .groupby("ward")
        .size()
        .reindex(ward_total.index)
        .fillna(0)
        .astype(int)
    )
    comp_per_ward = (ward_total - mcd_per_ward).astype(int)

    ward_comp = {
        "labels":     [_ward_label(w) for w in ward_total.index],
        "mcd":        mcd_per_ward.tolist(),
        "competitor": comp_per_ward.tolist(),
    }

    return dict(kpis=kpis, brand_count=brand_count, top_mcd_outlets=top_mcd_outlets,
                brand_reviews=brand_reviews, ward_comp=ward_comp)


def build_html(d: dict) -> str:
    k  = d["kpis"]
    bc = d["brand_count"]
    tm = d["top_mcd_outlets"]
    br = d["brand_reviews"]
    wc = d["ward_comp"]

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Competitor Landscape Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.2/dist/chart.umd.min.js"></script>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    background: #F0F2F5;
    color: #1a1a1a;
  }}

  /* ── Header ──────────────────────────────────────────────── */
  .header {{
    background: #1a1a2e;
    color: white;
    padding: 18px 28px;
    display: flex;
    align-items: center;
    gap: 14px;
  }}
  .header-title {{ font-size: 20px; font-weight: 700; }}
  .header-sub   {{ font-size: 13px; color: #aaa; margin-top: 2px; }}
  .header-badge {{
    margin-left: auto;
    background: #DA291C;
    color: white;
    font-size: 11px;
    font-weight: 600;
    padding: 4px 10px;
    border-radius: 12px;
    letter-spacing: 0.5px;
  }}

  /* ── Layout ──────────────────────────────────────────────── */
  .dashboard {{ padding: 20px 24px; }}

  /* ── KPI row ─────────────────────────────────────────────── */
  .kpi-row {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-bottom: 20px;
  }}
  .kpi-card {{
    background: white;
    border-radius: 10px;
    padding: 18px 20px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    border-left: 4px solid #ccc;
  }}
  .kpi-card.red    {{ border-left-color: #DA291C; }}
  .kpi-card.blue   {{ border-left-color: #1565C0; }}
  .kpi-card.purple {{ border-left-color: #7B1FA2; }}
  .kpi-card.teal   {{ border-left-color: #00695C; }}
  .kpi-value {{
    font-size: 32px;
    font-weight: 700;
    line-height: 1.1;
    margin-bottom: 4px;
  }}
  .kpi-label {{ font-size: 12px; color: #666; text-transform: uppercase; letter-spacing: 0.5px; }}

  /* ── Charts grid ─────────────────────────────────────────── */
  .charts-grid {{
    display: grid;
    grid-template-columns: 1fr;
    gap: 16px;
  }}
  .charts-row {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
  }}
  .chart-card {{
    background: white;
    border-radius: 10px;
    padding: 20px 22px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
  }}
  .chart-header {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;
  }}
  .chart-title {{
    font-size: 13px;
    font-weight: 600;
    color: #444;
    text-transform: uppercase;
    letter-spacing: 0.4px;
  }}
  .legend {{
    display: flex;
    gap: 14px;
    flex-wrap: wrap;
  }}
  .legend-item {{
    display: flex;
    align-items: center;
    gap: 5px;
    font-size: 11px;
    color: #555;
  }}
  .legend-dot {{
    width: 10px; height: 10px;
    border-radius: 50%;
    flex-shrink: 0;
  }}
  .chart-wrap {{ position: relative; }}
  .chart-wrap.tall   {{ height: 340px; }}
  .chart-wrap.medium {{ height: 280px; }}
  .chart-wrap.short  {{ height: 240px; }}
  .sort-btn {{
    font-size: 11px;
    padding: 3px 9px;
    border: 1px solid #ddd;
    border-radius: 4px;
    background: #f5f5f5;
    cursor: pointer;
    color: #555;
    white-space: nowrap;
  }}
  .sort-btn:hover {{ background: #e8e8e8; }}
</style>
</head>
<body>

<div class="header">
  <div>
    <div class="header-title">Competitor Landscape Dashboard</div>
    <div class="header-sub">Tokyo 23 Wards — Restaurant Data</div>
  </div>
  <div class="header-badge">Demo</div>
</div>

<div class="dashboard">

  <!-- KPI row -->
  <div class="kpi-row">
    <div class="kpi-card red">
      <div class="kpi-value">{k["total"]:,}</div>
      <div class="kpi-label">Total Restaurants</div>
    </div>
    <div class="kpi-card blue">
      <div class="kpi-value">{k["n_own"]:,}</div>
      <div class="kpi-label">M Outlets</div>
    </div>
    <div class="kpi-card purple">
      <div class="kpi-value">{k["n_brands"]}</div>
      <div class="kpi-label">Competitor Brands</div>
    </div>
    <div class="kpi-card teal">
      <div class="kpi-value">{k["total_reviews"]:,}</div>
      <div class="kpi-label">Total Reviews Scraped</div>
    </div>
  </div>

  <!-- Global colour legend -->
  <div style="display:flex;align-items:center;gap:20px;margin-bottom:12px;
              background:white;border-radius:8px;padding:10px 18px;
              box-shadow:0 1px 4px rgba(0,0,0,0.08);">
    <span style="font-size:11px;font-weight:600;color:#888;text-transform:uppercase;letter-spacing:0.4px;">Category</span>
    <div class="legend">
      <div class="legend-item"><div class="legend-dot" style="background:#FFC72C"></div>McDonald's</div>
      <div class="legend-item"><div class="legend-dot" style="background:#E65100"></div>Burger (direct)</div>
      <div class="legend-item"><div class="legend-dot" style="background:#7B1FA2"></div>Teishoku (indirect)</div>
      <div class="legend-item"><div class="legend-dot" style="background:#00695C"></div>Family (indirect)</div>
    </div>
  </div>

  <!-- Charts -->
  <div class="charts-grid">

    <!-- Top row: Top 10 M outlets + Brand count -->
    <div class="charts-row">

      <!-- Top 10 McDonald's by reviews -->
      <div class="chart-card">
        <div class="chart-header">
          <div class="chart-title">Top 10 Most Popular M Outlets</div>
          <button class="sort-btn" id="btnTopMcd" onclick="toggleSort('topMcd')">↑ Asc</button>
        </div>
        <div class="chart-wrap medium"><canvas id="chartTopMcd"></canvas></div>
      </div>

      <!-- Brand location count -->
      <div class="chart-card">
        <div class="chart-header">
          <div class="chart-title">Locations by Brand</div>
          <button class="sort-btn" id="btnBrandCount" onclick="toggleSort('brandCount')">↑ Asc</button>
        </div>
        <div class="chart-wrap medium"><canvas id="chartBrandCount"></canvas></div>
      </div>

    </div>

    <!-- Bottom row -->
    <div class="charts-row">

      <!-- Avg reviews by brand -->
      <div class="chart-card">
        <div class="chart-header">
          <div class="chart-title">Avg Reviews per Outlet — Popularity Proxy</div>
          <button class="sort-btn" id="btnAvgReview" onclick="toggleSort('avgReview')">↓ Desc</button>
        </div>
        <div class="chart-wrap short"><canvas id="chartAvgReview"></canvas></div>
      </div>

      <!-- Ward competition -->
      <div class="chart-card">
        <div class="chart-header">
          <div class="chart-title">Ward Competition (Top 15)</div>
          <button class="sort-btn" id="btnWard" onclick="toggleSort('ward')">↓ Desc</button>
        </div>
        <div class="chart-wrap short"><canvas id="chartWard"></canvas></div>
      </div>

    </div>
  </div>
</div>

<script>
Chart.defaults.font.family = "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif";
Chart.defaults.font.size   = 12;
Chart.defaults.color       = "#555";
const gridColor = "rgba(0,0,0,0.06)";

/* ── Raw data ───────────────────────────────────────────────── */
const dataTopMcd    = {{ labels: {_j(tm["labels"])},  values: {_j(tm["values"])}, colors: null }};
const dataBrandCount= {{ labels: {_j(bc["labels"])},  values: {_j(bc["values"])}, colors: {_j(bc["colors"])} }};
const dataAvgReview = {{ labels: {_j(br["labels"])},  values: {_j(br["values"])}, colors: {_j(br["colors"])} }};
const dataWard      = {{ labels: {_j(wc["labels"])},  mcd: {_j(wc["mcd"])},       comp: {_j(wc["competitor"])} }};

/* ── Sort state (true = ascending) ─────────────────────────── */
const sortAsc = {{ topMcd: true, brandCount: true, avgReview: false, ward: false }};
const btnText = asc => asc ? "↑ Asc" : "↓ Desc";

/* ── Generic single-dataset sort helper ─────────────────────── */
function applySort(chart, data, asc) {{
  const rows = data.labels.map((l, i) => ({{
    l, v: data.values[i], c: data.colors ? data.colors[i] : null
  }}));
  rows.sort((a, b) => asc ? a.v - b.v : b.v - a.v);
  chart.data.labels = rows.map(r => r.l);
  chart.data.datasets[0].data   = rows.map(r => r.v);
  if (data.colors) chart.data.datasets[0].backgroundColor = rows.map(r => r.c);
  chart.update();
}}

/* ── Ward stacked sort (by total) ───────────────────────────── */
function applyWardSort(asc) {{
  const rows = dataWard.labels.map((l, i) => ({{
    l, m: dataWard.mcd[i], c: dataWard.comp[i], t: dataWard.mcd[i] + dataWard.comp[i]
  }}));
  rows.sort((a, b) => asc ? a.t - b.t : b.t - a.t);
  chartWard.data.labels            = rows.map(r => r.l);
  chartWard.data.datasets[0].data  = rows.map(r => r.m);
  chartWard.data.datasets[1].data  = rows.map(r => r.c);
  chartWard.update();
}}

/* ── Toggle handler ─────────────────────────────────────────── */
function toggleSort(id) {{
  sortAsc[id] = !sortAsc[id];
  const asc = sortAsc[id];
  document.getElementById("btn" + id.charAt(0).toUpperCase() + id.slice(1)).textContent = btnText(asc);
  if      (id === "topMcd")     applySort(chartTopMcd,     dataTopMcd,     asc);
  else if (id === "brandCount") applySort(chartBrandCount, dataBrandCount, asc);
  else if (id === "avgReview")  applySort(chartAvgReview,  dataAvgReview,  asc);
  else if (id === "ward")       applyWardSort(asc);
}}

/* ── Chart: Top 10 McDonald's ───────────────────────────────── */
const chartTopMcd = new Chart(document.getElementById("chartTopMcd"), {{
  type: "bar",
  data: {{
    labels: [...dataTopMcd.labels],
    datasets: [{{ label: "Reviews", data: [...dataTopMcd.values],
      backgroundColor: "#FFC72C", borderRadius: 4, borderSkipped: false }}]
  }},
  options: {{
    indexAxis: "y", responsive: true, maintainAspectRatio: false,
    plugins: {{ legend: {{ display: false }},
      tooltip: {{ callbacks: {{ label: ctx => " " + ctx.parsed.x + " reviews" }} }} }},
    scales: {{
      x: {{ grid: {{ color: gridColor }} }},
      y: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 11 }} }} }}
    }}
  }}
}});

/* ── Chart: Locations by Brand ──────────────────────────────── */
const chartBrandCount = new Chart(document.getElementById("chartBrandCount"), {{
  type: "bar",
  data: {{
    labels: [...dataBrandCount.labels],
    datasets: [{{ label: "Outlets", data: [...dataBrandCount.values],
      backgroundColor: [...dataBrandCount.colors], borderRadius: 4, borderSkipped: false }}]
  }},
  options: {{
    indexAxis: "y", responsive: true, maintainAspectRatio: false,
    plugins: {{ legend: {{ display: false }},
      tooltip: {{ callbacks: {{ label: ctx => " " + ctx.parsed.x + " outlets" }} }} }},
    scales: {{
      x: {{ grid: {{ color: gridColor }}, ticks: {{ stepSize: 50 }} }},
      y: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 11 }} }} }}
    }}
  }}
}});

/* ── Chart: Avg Reviews per Brand ───────────────────────────── */
const chartAvgReview = new Chart(document.getElementById("chartAvgReview"), {{
  type: "bar",
  data: {{
    labels: [...dataAvgReview.labels],
    datasets: [{{ label: "Avg reviews", data: [...dataAvgReview.values],
      backgroundColor: [...dataAvgReview.colors], borderRadius: 4 }}]
  }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    plugins: {{ legend: {{ display: false }},
      tooltip: {{ callbacks: {{ label: ctx => " " + ctx.parsed.y.toFixed(1) + " avg reviews" }} }} }},
    scales: {{
      x: {{ grid: {{ display: false }} }},
      y: {{ grid: {{ color: gridColor }}, ticks: {{ stepSize: 20 }} }}
    }}
  }}
}});

/* ── Chart: Ward Competition ────────────────────────────────── */
const chartWard = new Chart(document.getElementById("chartWard"), {{
  type: "bar",
  data: {{
    labels: [...dataWard.labels],
    datasets: [
      {{ label: "M",           data: [...dataWard.mcd],  backgroundColor: "#FFC72C", borderRadius: 0 }},
      {{ label: "Competitors", data: [...dataWard.comp], backgroundColor: "#90A4AE", borderRadius: 4 }}
    ]
  }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    plugins: {{ legend: {{ position: "bottom", labels: {{ padding: 12, boxWidth: 12 }} }} }},
    scales: {{
      x: {{ stacked: true, grid: {{ display: false }}, ticks: {{ font: {{ size: 10 }} }} }},
      y: {{ stacked: true, grid: {{ color: gridColor }} }}
    }}
  }}
}});
</script>
</body>
</html>"""


def main():
    Path(OUTPUT_DIR).mkdir(exist_ok=True)

    print("Loading data...")
    all_df, own_df, comp_df = load_all_restaurants()
    print(f"  {len(all_df):,} restaurants loaded")

    print("Building dashboard data...")
    data = build_data(all_df, own_df, comp_df)

    print("Generating HTML...")
    html = build_html(data)

    out = Path(OUTPUT_DASHBOARD)
    out.write_text(html, encoding="utf-8")
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()
