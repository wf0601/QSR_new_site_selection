// McDonald's Tokyo — Technical Deck
// Audience: data scientists / engineers
// Run: node make_tech_deck.js

const pptxgen = require("pptxgenjs");

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.title  = "McDonald's Tokyo — Site Selection Pipeline";

const C = {
  BG:     "0D1B2A",
  PANEL:  "1B2838",
  TEAL:   "00897B",
  TEAL_L: "4DB6AC",
  AMBER:  "E65100",
  AMBER_L:"FF8A65",
  GREEN:  "1B5E20",
  GREEN_L:"66BB6A",
  WHITE:  "ECEFF1",
  MUTED:  "78909C",
  LIGHT:  "B0BEC5",
  GOLD:   "FFC72C",
  RED:    "DA291C",
};

const mkShadow = () => ({ type: "outer", color: "000000", blur: 10, offset: 3, angle: 135, opacity: 0.25 });

// ── Slide 1: Title ────────────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.BG };

  // Teal left bar
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 0.3, h: 5.625, fill: { color: C.TEAL }, line: { color: C.TEAL } });

  // Code tag
  s.addShape(pres.shapes.RECTANGLE, { x: 0.6, y: 0.5, w: 3.8, h: 0.45, fill: { color: C.PANEL }, line: { color: C.TEAL } });
  s.addText("# site-selection-pipeline  v2.0", {
    x: 0.6, y: 0.5, w: 3.8, h: 0.45,
    fontSize: 10, fontFace: "Consolas", color: C.TEAL_L, align: "left", valign: "middle", margin: 5,
  });

  s.addText("McDonald's Tokyo", {
    x: 0.6, y: 1.2, w: 9.1, h: 0.85,
    fontSize: 42, fontFace: "Arial Black", bold: true, color: C.WHITE, margin: 0,
  });
  s.addText("Site Selection Pipeline", {
    x: 0.6, y: 2.05, w: 9.1, h: 0.6,
    fontSize: 26, fontFace: "Arial", color: C.TEAL_L, margin: 0,
  });

  // Divider
  s.addShape(pres.shapes.RECTANGLE, { x: 0.6, y: 3.05, w: 8.8, h: 0.04, fill: { color: C.PANEL }, line: { color: C.PANEL } });

  // Key stats row
  const stats = [
    { n: "1,804",  label: "restaurants"       },
    { n: "110",    label: "demand clusters"   },
    { n: "3,572",  label: "candidates scored" },
    { n: "50",     label: "sites selected"    },
  ];
  stats.forEach((st, i) => {
    const x = 0.6 + i * 2.35;
    s.addText(st.n, {
      x, y: 3.2, w: 2.2, h: 0.65,
      fontSize: 30, fontFace: "Arial Black", bold: true, color: C.TEAL_L, align: "left", margin: 0,
    });
    s.addText(st.label, {
      x, y: 3.85, w: 2.2, h: 0.3,
      fontSize: 10, fontFace: "Arial", color: C.MUTED, align: "left", margin: 0,
    });
  });

  s.addText("HDBSCAN  ·  Noise Reassignment  ·  Greedy NMS  ·  Folium Interactive Map", {
    x: 0.6, y: 4.95, w: 8.8, h: 0.3,
    fontSize: 9, fontFace: "Consolas", color: C.MUTED, align: "left", margin: 0,
  });
}

// ── Slide 2: Data Sources ─────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.BG };

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.75, fill: { color: C.PANEL }, line: { color: C.PANEL } });
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 0.3,  h: 0.75, fill: { color: C.TEAL  }, line: { color: C.TEAL  } });
  s.addText("Data Sources & Scraping", {
    x: 0.5, y: 0, w: 9.1, h: 0.75,
    fontSize: 20, fontFace: "Arial Black", bold: true, color: C.WHITE, align: "left", valign: "middle", margin: 0,
  });

  s.addText("Source: Tabelog Tokyo  —  1,804 restaurants, scraped via scraper.py", {
    x: 0.5, y: 0.88, w: 9, h: 0.35,
    fontSize: 11, fontFace: "Arial", color: C.LIGHT, margin: 0,
  });

  // Header row
  const cols = { tier: 0.5, brands: 2.5, count: 7.15, weight: 8.3 };
  [["Category", cols.tier], ["Key Brands", cols.brands], ["Count", cols.count], ["Weight", cols.weight]].forEach(([h, x]) => {
    s.addText(h, { x, y: 1.35, w: 1.5, h: 0.3, fontSize: 9, fontFace: "Arial Black", color: C.MUTED, margin: 0 });
  });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 1.65, w: 9, h: 0.03, fill: { color: C.PANEL }, line: { color: C.PANEL } });

  const tiers = [
    { tier: "Burger (direct)",     brands: "McDonald's · MOS Burger · KFC · Wendy's",    count: "564",  weight: "1.0", col: C.RED    },
    { tier: "Teishoku (indirect)", brands: "Matsuya · Yoshinoya · Sukiya · Nakau",        count: "960",  weight: "0.5", col: C.AMBER  },
    { tier: "Family (indirect)",   brands: "Gusto · Saizeriya",                           count: "281",  weight: "0.3", col: C.TEAL   },
  ];
  tiers.forEach((t, i) => {
    const y = 1.75 + i * 0.9;
    s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: y - 0.06, w: 9, h: 0.78, fill: { color: C.PANEL }, line: { color: C.PANEL } });
    s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: y - 0.06, w: 0.06, h: 0.78, fill: { color: t.col }, line: { color: t.col } });
    s.addText(t.tier,   { x: 0.7,       y, w: 1.7, h: 0.35, fontSize: 11, fontFace: "Arial Black", color: C.WHITE, margin: 0 });
    s.addText(t.brands, { x: cols.brands, y, w: 4.5, h: 0.35, fontSize: 10, fontFace: "Arial",       color: C.LIGHT, margin: 0 });
    s.addText(t.count,  { x: cols.count,  y, w: 1.0, h: 0.35, fontSize: 13, fontFace: "Arial Black", color: t.col,   align: "center", margin: 0 });
    s.addText(t.weight, { x: cols.weight, y, w: 1.0, h: 0.35, fontSize: 12, fontFace: "Consolas",    color: C.TEAL_L, align: "center", margin: 0 });
  });

  s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 4.7, w: 9, h: 0.62, fill: { color: C.PANEL }, line: { color: C.PANEL } });
  s.addText([
    { text: "review_count", options: { color: C.TEAL_L } },
    { text: " used as popularity proxy  ·  ", options: { color: C.MUTED } },
    { text: "weight", options: { color: C.TEAL_L } },
    { text: " applied only to competitive-pressure distance filter  ·  HDBSCAN clustering uses raw counts", options: { color: C.MUTED } },
  ], {
    x: 0.65, y: 4.7, w: 8.7, h: 0.62,
    fontSize: 9, fontFace: "Consolas", valign: "middle", margin: 0,
  });
}

// ── Slide 3: Pipeline Architecture ───────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.BG };

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.75, fill: { color: C.PANEL }, line: { color: C.PANEL } });
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 0.3,  h: 0.75, fill: { color: C.TEAL  }, line: { color: C.TEAL  } });
  s.addText("Pipeline Architecture", {
    x: 0.5, y: 0, w: 9.1, h: 0.75,
    fontSize: 20, fontFace: "Arial Black", bold: true, color: C.WHITE, align: "left", valign: "middle", margin: 0,
  });

  const stages = [
    { n: "1", step: "Scrape",   file: "scraper.py",           desc: "Tabelog → CSV\n1,804 restaurants",     col: C.TEAL   },
    { n: "2", step: "Cluster",  file: "site_selection.py",    desc: "HDBSCAN\n110 demand zones",            col: C.TEAL   },
    { n: "3", step: "Score",    file: "site_selection_v2.py", desc: "3-factor scoring\n3,572 candidates",   col: C.AMBER  },
    { n: "4", step: "Select",   file: "app_interactive.py",   desc: "Greedy NMS\n50 final sites",           col: C.GREEN_L },
  ];

  stages.forEach((p, i) => {
    const x = 0.4 + i * 2.35, y = 1.1, w = 2.1, h = 3.7;
    s.addShape(pres.shapes.RECTANGLE, { x, y, w, h, fill: { color: C.PANEL }, line: { color: p.col, width: 1.5 }, shadow: mkShadow() });
    s.addShape(pres.shapes.RECTANGLE, { x, y, w, h: 0.06, fill: { color: p.col }, line: { color: p.col } });

    s.addShape(pres.shapes.OVAL, { x: x + w / 2 - 0.38, y: y + 0.2, w: 0.76, h: 0.76, fill: { color: p.col }, line: { color: p.col } });
    s.addText(p.n, {
      x: x + w / 2 - 0.38, y: y + 0.2, w: 0.76, h: 0.76,
      fontSize: 20, fontFace: "Arial Black", bold: true, color: C.BG, align: "center", valign: "middle", margin: 0,
    });

    s.addText(p.step, {
      x: x + 0.1, y: y + 1.1, w: w - 0.2, h: 0.45,
      fontSize: 16, fontFace: "Arial Black", bold: true, color: p.col, align: "center", margin: 0,
    });
    s.addText(p.desc, {
      x: x + 0.15, y: y + 1.65, w: w - 0.3, h: 0.85,
      fontSize: 11, fontFace: "Arial", color: C.LIGHT, align: "center", margin: 0,
    });
    s.addShape(pres.shapes.RECTANGLE, { x: x + 0.18, y: y + 2.72, w: w - 0.36, h: 0.55, fill: { color: C.BG }, line: { color: C.PANEL } });
    s.addText(p.file, {
      x: x + 0.18, y: y + 2.72, w: w - 0.36, h: 0.55,
      fontSize: 8, fontFace: "Consolas", color: p.col, align: "center", valign: "middle", margin: 0,
    });

    if (i < 3) {
      s.addShape(pres.shapes.RECTANGLE, {
        x: x + w + 0.02, y: y + h / 2 - 0.04, w: 0.22, h: 0.08,
        fill: { color: C.MUTED }, line: { color: C.MUTED },
      });
    }
  });

  s.addText("output/interactive_map_slider.html   +   output/top_candidates_v2.csv", {
    x: 0.5, y: 5.05, w: 9, h: 0.35,
    fontSize: 9.5, fontFace: "Consolas", color: C.TEAL_L, margin: 0,
  });
}

// ── Slide 4: HDBSCAN Clustering ───────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.BG };

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.75, fill: { color: C.PANEL }, line: { color: C.PANEL } });
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 0.3,  h: 0.75, fill: { color: C.TEAL  }, line: { color: C.TEAL  } });
  s.addText("HDBSCAN Demand Clustering", {
    x: 0.5, y: 0, w: 9.1, h: 0.75,
    fontSize: 20, fontFace: "Arial Black", bold: true, color: C.WHITE, align: "left", valign: "middle", margin: 0,
  });

  // Params column
  s.addText("Parameters", {
    x: 0.5, y: 0.9, w: 4, h: 0.4,
    fontSize: 12, fontFace: "Arial Black", color: C.TEAL_L, margin: 0,
  });
  const params = [
    ["metric",              "haversine  (input: radians)"],
    ["min_cluster_size",    "15"],
    ["min_samples",         "5"],
    ["cluster_selection",   "eom"],
    ["prediction_data",     "True"],
  ];
  params.forEach(([k, v], i) => {
    const y = 1.38 + i * 0.6;
    s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y, w: 4.3, h: 0.5, fill: { color: C.PANEL }, line: { color: C.PANEL } });
    s.addText(k, { x: 0.65, y: y + 0.08, w: 1.9, h: 0.3, fontSize: 9.5, fontFace: "Consolas", color: C.MUTED,  margin: 0 });
    s.addText(v, { x: 2.65, y: y + 0.08, w: 2.0, h: 0.3, fontSize: 9.5, fontFace: "Consolas", color: C.TEAL_L, margin: 0 });
  });

  // Weighting box
  s.addText("Review-Count Weighting", {
    x: 5.3, y: 0.9, w: 4.2, h: 0.4,
    fontSize: 12, fontFace: "Arial Black", color: C.AMBER_L, margin: 0,
  });
  s.addShape(pres.shapes.RECTANGLE, { x: 5.3, y: 1.38, w: 4.2, h: 2.62, fill: { color: C.PANEL }, line: { color: C.AMBER_L, width: 1 }, shadow: mkShadow() });
  s.addText([
    { text: "HDBSCAN has no sample_weight.\n", options: { color: C.LIGHT } },
    { text: "Row replication achieves the same effect:\n\n", options: { color: C.LIGHT } },
    { text: "repeats = (review_count / Q25)\n", options: { color: C.TEAL_L } },
    { text: "        .round().clip(1, 10)\n\n", options: { color: C.TEAL_L } },
    { text: "Q25 = 18 reviews  →  1× repeat\n", options: { color: C.MUTED } },
    { text: "High-review restaurants  →  up to 10×\n\n", options: { color: C.MUTED } },
    { text: "1,804 restaurants  →  4,174 weighted points", options: { color: C.AMBER_L } },
  ], {
    x: 5.5, y: 1.52, w: 3.85, h: 2.35,
    fontSize: 9.5, fontFace: "Consolas", margin: 0,
  });

  s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 5.0, w: 9, h: 0.45, fill: { color: C.PANEL }, line: { color: C.TEAL, width: 1.5 } });
  s.addText("Result:  110 demand clusters  ·  438 noise-labelled restaurants  ·  haversine on radians input", {
    x: 0.65, y: 5.0, w: 8.7, h: 0.45,
    fontSize: 9.5, fontFace: "Consolas", color: C.TEAL_L, valign: "middle", margin: 0,
  });
}

// ── Slide 5: Sparse Area Recovery ─────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.BG };

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.75, fill: { color: C.PANEL }, line: { color: C.PANEL } });
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 0.3,  h: 0.75, fill: { color: C.AMBER }, line: { color: C.AMBER } });
  s.addText("v2 Improvement — Sparse Area Recovery", {
    x: 0.5, y: 0, w: 9.1, h: 0.75,
    fontSize: 20, fontFace: "Arial Black", bold: true, color: C.WHITE, align: "left", valign: "middle", margin: 0,
  });

  // Problem card
  const cw = 4.3;
  s.addShape(pres.shapes.RECTANGLE, { x: 0.4, y: 0.9, w: cw, h: 4.5, fill: { color: C.PANEL }, line: { color: C.AMBER, width: 1.5 }, shadow: mkShadow() });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.4, y: 0.9, w: cw, h: 0.07, fill: { color: C.AMBER }, line: { color: C.AMBER } });
  s.addText("v1 Problem", { x: 0.6, y: 1.05, w: cw - 0.3, h: 0.42, fontSize: 13, fontFace: "Arial Black", color: C.AMBER_L, margin: 0 });
  s.addText([
    { text: "Shirokane: 14 restaurants spread\nacross a large area.\n\n", options: { color: C.LIGHT } },
    { text: "HDBSCAN assigns label = -1 (noise).\n\n", options: { color: C.AMBER_L } },
    { text: "438 restaurants discarded.\nZero candidates in that zone.\n\n", options: { color: C.LIGHT } },
    { text: "Yet Shirokane has thousands of\noffice workers eating lunch daily.", options: { color: C.MUTED } },
  ], {
    x: 0.6, y: 1.6, w: cw - 0.35, h: 3.65,
    fontSize: 10.5, fontFace: "Arial", margin: 0,
  });

  // Fix card
  s.addShape(pres.shapes.RECTANGLE, { x: 5.3, y: 0.9, w: cw, h: 4.5, fill: { color: C.PANEL }, line: { color: C.GREEN_L, width: 1.5 }, shadow: mkShadow() });
  s.addShape(pres.shapes.RECTANGLE, { x: 5.3, y: 0.9, w: cw, h: 0.07, fill: { color: C.GREEN_L }, line: { color: C.GREEN_L } });
  s.addText("v2 Fix", { x: 5.5, y: 1.05, w: cw - 0.3, h: 0.42, fontSize: 13, fontFace: "Arial Black", color: C.GREEN_L, margin: 0 });
  s.addText([
    { text: "1. Compute centroids from confirmed\n   members only.\n\n", options: { color: C.LIGHT } },
    { text: "2. For each noise point:\n   ", options: { color: C.LIGHT } },
    { text: "label = nearest_centroid\n", options: { color: C.TEAL_L } },
    { text: "   (BallTree haversine)\n\n", options: { color: C.TEAL_L } },
    { text: "3. Set membership_strength:\n   ", options: { color: C.LIGHT } },
    { text: "= NOISE_MEMBERSHIP  (slider 0–1)\n\n", options: { color: C.GREEN_L } },
    { text: "Shirokane → rank #48\n(amber badge, interactive map)", options: { color: C.AMBER_L } },
  ], {
    x: 5.5, y: 1.6, w: cw - 0.35, h: 3.65,
    fontSize: 10.5, fontFace: "Consolas", margin: 0,
  });
}

// ── Slide 6: Scoring Formula ──────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.BG };

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.75, fill: { color: C.PANEL }, line: { color: C.PANEL } });
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 0.3,  h: 0.75, fill: { color: C.TEAL  }, line: { color: C.TEAL  } });
  s.addText("Scoring Formula", {
    x: 0.5, y: 0, w: 9.1, h: 0.75,
    fontSize: 20, fontFace: "Arial Black", bold: true, color: C.WHITE, align: "left", valign: "middle", margin: 0,
  });

  // Formula block
  s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 0.9, w: 9, h: 1.15, fill: { color: C.PANEL }, line: { color: C.TEAL, width: 1.5 }, shadow: mkShadow() });
  s.addText([
    { text: "base_score  = ", options: { color: C.MUTED } },
    { text: "0.40", options: { color: C.TEAL_L, bold: true } },
    { text: " × cluster_demand  +  ", options: { color: C.MUTED } },
    { text: "0.40", options: { color: C.AMBER_L, bold: true } },
    { text: " × mcd_gap  +  ", options: { color: C.MUTED } },
    { text: "0.20", options: { color: C.GREEN_L, bold: true } },
    { text: " × distance_buffer", options: { color: C.MUTED } },
  ], { x: 0.7, y: 1.0, w: 8.6, h: 0.45, fontSize: 13, fontFace: "Consolas", margin: 0 });
  s.addText([
    { text: "final_score = ", options: { color: C.MUTED } },
    { text: "base_score", options: { color: C.WHITE } },
    { text: " × ", options: { color: C.MUTED } },
    { text: "membership_strength", options: { color: C.GOLD } },
    { text: "  /  max(all raw scores)", options: { color: C.MUTED } },
  ], { x: 0.7, y: 1.5, w: 8.6, h: 0.4, fontSize: 13, fontFace: "Consolas", margin: 0 });

  // Component cards
  const comps = [
    { w: "0.40", name: "cluster_demand",  desc: "sum(review_count) in the zone,\nnormalised by global max.\nHow review-rich is the area?",    col: C.TEAL_L  },
    { w: "0.40", name: "mcd_gap",         desc: "1 − (mcd_count / n_restaurants)\nin the cluster.\nHow absent is McDonald's?",               col: C.AMBER_L },
    { w: "0.20", name: "distance_buffer", desc: "dist_to_nearest_own\nclipped at 2 km, divided by 2.\nSafe spacing from existing stores.",  col: C.GREEN_L },
  ];
  comps.forEach((c, i) => {
    const x = 0.5 + i * 3.1, y = 2.3, w = 2.85, h = 2.65;
    s.addShape(pres.shapes.RECTANGLE, { x, y, w, h, fill: { color: C.PANEL }, line: { color: c.col, width: 1.5 }, shadow: mkShadow() });
    s.addShape(pres.shapes.RECTANGLE, { x: x + 0.18, y: y + 0.2, w: 0.72, h: 0.5, fill: { color: c.col }, line: { color: c.col } });
    s.addText(c.w, {
      x: x + 0.18, y: y + 0.2, w: 0.72, h: 0.5,
      fontSize: 15, fontFace: "Arial Black", bold: true, color: C.BG, align: "center", valign: "middle", margin: 0,
    });
    s.addText(c.name, { x: x + 0.18, y: y + 0.85, w: w - 0.36, h: 0.4,  fontSize: 11, fontFace: "Consolas", color: c.col, margin: 0 });
    s.addText(c.desc, { x: x + 0.18, y: y + 1.35, w: w - 0.36, h: 1.15, fontSize: 10, fontFace: "Arial",    color: C.LIGHT, margin: 0 });
  });

  s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 5.1, w: 9, h: 0.35, fill: { color: C.PANEL }, line: { color: C.PANEL } });
  s.addText([
    { text: "membership_strength: ", options: { color: C.MUTED } },
    { text: "approx_predict", options: { color: C.TEAL_L } },
    { text: " confidence for confirmed clusters  ·  ", options: { color: C.MUTED } },
    { text: "NOISE_MEMBERSHIP", options: { color: C.GOLD } },
    { text: " (slider) for sparse-area candidates", options: { color: C.MUTED } },
  ], { x: 0.65, y: 5.1, w: 8.7, h: 0.35, fontSize: 8.5, fontFace: "Consolas", valign: "middle", margin: 0 });
}

// ── Slide 7: Greedy NMS Selection ─────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.BG };

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.75, fill: { color: C.PANEL }, line: { color: C.PANEL } });
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 0.3,  h: 0.75, fill: { color: C.GREEN_L }, line: { color: C.GREEN_L } });
  s.addText("Greedy NMS Candidate Selection", {
    x: 0.5, y: 0, w: 9.1, h: 0.75,
    fontSize: 20, fontFace: "Arial Black", bold: true, color: C.WHITE, align: "left", valign: "middle", margin: 0,
  });

  const funnel = [
    { label: "Candidate grid",           n: "8,484",  note: "0.003° spacing  ≈ 330 m",    col: C.TEAL   },
    { label: "dist_to_own_km  ≥  0.8",   n: "",       note: "Cannibalization guard",       col: C.AMBER  },
    { label: "dist_to_comp_km  ≤  3.0",  n: "3,572",  note: "Must be near market activity",col: C.AMBER  },
    { label: "Greedy NMS  (1.5 km)",     n: "50",     note: "Geographic diversity",        col: C.GREEN_L },
  ];
  funnel.forEach((f, i) => {
    const indent = i * 0.5, y = 0.95 + i * 1.05;
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.5 + indent, y, w: 9 - indent * 2, h: 0.8,
      fill: { color: C.PANEL }, line: { color: f.col, width: 1.5 }, shadow: mkShadow(),
    });
    if (i > 0) {
      s.addShape(pres.shapes.RECTANGLE, { x: 4.8, y: y - 0.23, w: 0.08, h: 0.23, fill: { color: C.MUTED }, line: { color: C.MUTED } });
    }
    s.addText(f.label, {
      x: 0.8 + indent, y: y + 0.08, w: 5.5, h: 0.6,
      fontSize: 13, fontFace: "Consolas", color: f.col, valign: "middle", margin: 0,
    });
    if (f.n) {
      s.addText(f.n, {
        x: 6.5, y: y + 0.08, w: 1.4, h: 0.6,
        fontSize: 17, fontFace: "Arial Black", bold: true, color: f.col, align: "right", valign: "middle", margin: 0,
      });
    }
    s.addText(f.note, {
      x: 8.0, y: y + 0.08, w: 1.4, h: 0.6,
      fontSize: 8.5, fontFace: "Arial", color: C.MUTED, align: "left", valign: "middle", margin: 0,
    });
  });

  s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 5.08, w: 9, h: 0.42, fill: { color: C.PANEL }, line: { color: C.GREEN_L, width: 1.5 } });
  s.addText("sort desc by score  →  select candidate  →  suppress all within 1.5 km  →  repeat until 50 selected", {
    x: 0.65, y: 5.08, w: 8.7, h: 0.42,
    fontSize: 9, fontFace: "Consolas", color: C.GREEN_L, valign: "middle", margin: 0,
  });
}

// ── Slide 8: Results ──────────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.BG };

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.75, fill: { color: C.PANEL }, line: { color: C.PANEL } });
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 0.3,  h: 0.75, fill: { color: C.TEAL  }, line: { color: C.TEAL  } });
  s.addText("Results & Output", {
    x: 0.5, y: 0, w: 9.1, h: 0.75,
    fontSize: 20, fontFace: "Arial Black", bold: true, color: C.WHITE, align: "left", valign: "middle", margin: 0,
  });

  const metrics = [
    { n: "21",    label: "Distinct clusters\nrepresented",   col: C.TEAL_L  },
    { n: "1.04",  label: "Avg km to\nnearest McD",          col: C.AMBER_L },
    { n: "0.788", label: "Mean normalised\nscore",           col: C.GREEN_L },
    { n: "4",     label: "Zero-gap\nopportunity zones",     col: C.GOLD    },
  ];
  metrics.forEach((m, i) => {
    const x = 0.5 + i * 2.3, y = 0.9;
    s.addShape(pres.shapes.RECTANGLE, { x, y, w: 2.05, h: 1.75, fill: { color: C.PANEL }, line: { color: m.col, width: 1.5 }, shadow: mkShadow() });
    s.addText(m.n, {
      x, y: y + 0.15, w: 2.05, h: 0.9,
      fontSize: 36, fontFace: "Arial Black", bold: true, color: m.col, align: "center", margin: 0,
    });
    s.addText(m.label, {
      x, y: y + 1.1, w: 2.05, h: 0.55,
      fontSize: 10, fontFace: "Arial", color: C.MUTED, align: "center", margin: 0,
    });
  });

  // Zone chart
  s.addChart(pres.charts.BAR, [{
    name: "Sites",
    labels: ["West Tokyo", "East Tokyo", "Central"],
    values: [25, 12, 11],
  }], {
    x: 0.5, y: 2.85, w: 5.3, h: 2.55,
    barDir: "bar",
    chartColors: ["DA291C", "E65100", "00897B"],
    chartArea: { fill: { color: C.PANEL }, roundedCorners: false },
    catAxisLabelColor: "90A4AE",
    valAxisLabelColor: "90A4AE",
    valGridLine: { color: "1B2838", size: 0.5 },
    catGridLine: { style: "none" },
    showValue: true,
    dataLabelColor: "ECEFF1",
    showLegend: false,
    showTitle: false,
  });

  // Output files
  s.addText("Output Files", {
    x: 6.1, y: 2.85, w: 3.6, h: 0.4,
    fontSize: 12, fontFace: "Arial Black", color: C.TEAL_L, margin: 0,
  });
  const files = [
    { f: "interactive_map_slider.html", note: "Self-contained, no server needed" },
    { f: "interactive_map_v2.html",     note: "Static v2 reference map"         },
    { f: "top_candidates_v2.csv",       note: "Full ranked candidate table"      },
  ];
  files.forEach((fl, i) => {
    const y = 3.35 + i * 0.72;
    s.addShape(pres.shapes.RECTANGLE, { x: 6.1, y, w: 3.6, h: 0.6, fill: { color: C.PANEL }, line: { color: C.PANEL } });
    s.addShape(pres.shapes.RECTANGLE, { x: 6.1, y, w: 0.06, h: 0.6, fill: { color: C.TEAL }, line: { color: C.TEAL } });
    s.addText(fl.f,    { x: 6.25, y: y + 0.04, w: 3.3, h: 0.27, fontSize: 8.5, fontFace: "Consolas", color: C.TEAL_L, margin: 0 });
    s.addText(fl.note, { x: 6.25, y: y + 0.3,  w: 3.3, h: 0.22, fontSize: 8.5, fontFace: "Arial",    color: C.MUTED,  margin: 0 });
  });
}

pres.writeFile({ fileName: "output/tech_deck.pptx" })
  .then(() => console.log("✓  output/tech_deck.pptx"));
