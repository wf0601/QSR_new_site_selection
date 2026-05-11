// McDonald's Tokyo — Business Deck
// Audience: executives / non-technical stakeholders
// Run: node make_business_deck.js

const pptxgen = require("pptxgenjs");

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.title  = "McDonald's Tokyo — New Site Expansion Strategy";

const C = {
  RED:   "DA291C",
  GOLD:  "FFC72C",
  NAVY:  "1E2761",
  WHITE: "FFFFFF",
  GRAY:  "F5F5F5",
  LIGHT: "E0E0E0",
  DARK:  "1A1A1A",
  MID:   "555555",
  MUTED: "999999",
  CREAM: "FFF8E1",
  BROWN: "5D4037",
};

const mkShadow = () => ({ type: "outer", color: "000000", blur: 8, offset: 3, angle: 135, opacity: 0.12 });

// ── Slide 1: Title ────────────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.RED };

  // Gold stripes
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0,     w: 10, h: 0.15, fill: { color: C.GOLD }, line: { color: C.GOLD } });
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 5.475, w: 10, h: 0.15, fill: { color: C.GOLD }, line: { color: C.GOLD } });

  // M badge
  s.addShape(pres.shapes.OVAL, { x: 0.6, y: 0.75, w: 1.7, h: 1.7, fill: { color: C.GOLD }, line: { color: C.GOLD } });
  s.addText("M", { x: 0.6, y: 0.75, w: 1.7, h: 1.7, fontSize: 80, fontFace: "Arial Black", bold: true, color: C.RED, align: "center", valign: "middle", margin: 0 });

  // Headlines
  s.addText("McDonald's Tokyo", {
    x: 0.55, y: 2.7, w: 9.1, h: 0.85,
    fontSize: 44, fontFace: "Arial Black", bold: true, color: C.WHITE, align: "left", margin: 0,
  });
  s.addText("New Site Expansion Strategy", {
    x: 0.55, y: 3.55, w: 9.1, h: 0.55,
    fontSize: 24, fontFace: "Arial", color: C.GOLD, align: "left", margin: 0,
  });

  // Tag
  s.addShape(pres.shapes.RECTANGLE, { x: 0.55, y: 4.4, w: 3.8, h: 0.5, fill: { color: C.NAVY }, line: { color: C.NAVY }, shadow: mkShadow() });
  s.addText("Data-Driven Market Analysis  ·  Tokyo 2025", {
    x: 0.55, y: 4.4, w: 3.8, h: 0.5,
    fontSize: 10, fontFace: "Arial", color: C.WHITE, align: "center", valign: "middle", margin: 0,
  });
}

// ── Slide 2: Executive Summary ────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.WHITE };

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.85, fill: { color: C.RED }, line: { color: C.RED } });
  s.addText("Executive Summary", {
    x: 0.4, y: 0, w: 9.2, h: 0.85,
    fontSize: 22, fontFace: "Arial Black", bold: true, color: C.WHITE, align: "left", valign: "middle", margin: 0,
  });

  const stats = [
    { n: "1,804", label: "Restaurants\nAnalyzed"      },
    { n: "275",   label: "Existing\nMcDonald's"       },
    { n: "110",   label: "Demand Zones\nMapped"        },
    { n: "50",    label: "Priority Sites\nIdentified"  },
  ];
  stats.forEach((st, i) => {
    const x = 0.45 + i * 2.3, y = 1.2, w = 2.05, h = 2.5;
    s.addShape(pres.shapes.RECTANGLE, { x, y, w, h, fill: { color: C.GRAY }, line: { color: C.LIGHT }, shadow: mkShadow() });
    s.addShape(pres.shapes.RECTANGLE, { x, y, w, h: 0.07, fill: { color: C.RED }, line: { color: C.RED } });
    s.addText(st.n, {
      x, y: y + 0.3, w, h: 1.15,
      fontSize: 48, fontFace: "Arial Black", bold: true, color: C.RED, align: "center", margin: 0,
    });
    s.addText(st.label, {
      x, y: y + 1.6, w, h: 0.75,
      fontSize: 12, fontFace: "Arial", color: C.MID, align: "center", margin: 0,
    });
  });

  // Insight banner
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 4.85, w: 10, h: 0.775, fill: { color: C.CREAM }, line: { color: "FFE082" } });
  s.addText("Key Insight:  4 high-demand zones have zero McDonald's presence — untapped lunch & dinner markets ready for entry.", {
    x: 0.4, y: 4.85, w: 9.2, h: 0.775,
    fontSize: 11.5, fontFace: "Arial", color: C.BROWN, align: "left", valign: "middle", margin: 0,
  });
}

// ── Slide 3: Our Approach ─────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.WHITE };

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.85, fill: { color: C.NAVY }, line: { color: C.NAVY } });
  s.addText("Our Approach", {
    x: 0.4, y: 0, w: 9.2, h: 0.85,
    fontSize: 22, fontFace: "Arial Black", bold: true, color: C.WHITE, align: "left", valign: "middle", margin: 0,
  });

  const steps = [
    { n: "1", title: "Map Every Restaurant",  body: "Collected location and popularity data for 1,804 restaurants across Tokyo — McDonald's plus all major competitor chains." },
    { n: "2", title: "Find Demand Zones",      body: "Identified 110 natural dining hotspots by analysing where high-popularity restaurants cluster across the city." },
    { n: "3", title: "Score & Shortlist",      body: "Ranked 8,500 candidate locations by demand strength, McDonald's absence, and safe spacing from existing stores." },
  ];

  steps.forEach((st, i) => {
    const x = 0.45 + i * 3.15, y = 1.3, w = 2.85, h = 3.6;
    s.addShape(pres.shapes.RECTANGLE, { x, y, w, h, fill: { color: C.GRAY }, line: { color: C.LIGHT }, shadow: mkShadow() });

    s.addShape(pres.shapes.OVAL, { x: x + w / 2 - 0.42, y: y + 0.25, w: 0.84, h: 0.84, fill: { color: C.RED }, line: { color: C.RED } });
    s.addText(st.n, {
      x: x + w / 2 - 0.42, y: y + 0.25, w: 0.84, h: 0.84,
      fontSize: 24, fontFace: "Arial Black", bold: true, color: C.WHITE, align: "center", valign: "middle", margin: 0,
    });

    s.addText(st.title, {
      x: x + 0.15, y: y + 1.25, w: w - 0.3, h: 0.55,
      fontSize: 14, fontFace: "Arial Black", bold: true, color: C.DARK, align: "center", margin: 0,
    });
    s.addText(st.body, {
      x: x + 0.2, y: y + 1.95, w: w - 0.4, h: 1.5,
      fontSize: 11, fontFace: "Arial", color: C.MID, align: "center", margin: 0,
    });

    if (i < 2) {
      s.addShape(pres.shapes.RECTANGLE, {
        x: x + w + 0.03, y: y + h / 2 - 0.05, w: 0.27, h: 0.1,
        fill: { color: C.RED }, line: { color: C.RED },
      });
    }
  });
}

// ── Slide 4: Competitive Landscape ────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.WHITE };

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.85, fill: { color: C.RED }, line: { color: C.RED } });
  s.addText("Competitive Landscape", {
    x: 0.4, y: 0, w: 9.2, h: 0.85,
    fontSize: 22, fontFace: "Arial Black", bold: true, color: C.WHITE, align: "left", valign: "middle", margin: 0,
  });

  s.addChart(pres.charts.BAR, [{
    name: "Locations",
    labels: ["Teishoku\n(indirect)", "Burger rivals\n(direct)", "Family\n(indirect)", "McDonald's\n(own)"],
    values: [960, 289, 281, 275],
  }], {
    x: 0.4, y: 1.0, w: 5.6, h: 4.0,
    barDir: "bar",
    chartColors: ["9E9E9E", "FF7043", "BDBDBD", "DA291C"],
    chartArea: { fill: { color: C.WHITE }, roundedCorners: false },
    catAxisLabelColor: "555555",
    valAxisLabelColor: "555555",
    valGridLine: { color: "E0E0E0", size: 0.5 },
    catGridLine: { style: "none" },
    showValue: true,
    dataLabelColor: "333333",
    showLegend: false,
    showTitle: false,
  });

  const items = [
    { color: "DA291C", label: "McDonald's",          n: "275", note: "Own brand" },
    { color: "FF7043", label: "Burger chains",        n: "289", note: "Direct — same product category" },
    { color: "9E9E9E", label: "Teishoku / rice sets", n: "960", note: "Indirect — fast-casual lunch" },
    { color: "BDBDBD", label: "Family restaurants",   n: "281", note: "Indirect — sit-down dining" },
  ];
  items.forEach((it, i) => {
    const y = 1.5 + i * 0.9;
    s.addShape(pres.shapes.RECTANGLE, { x: 6.3, y, w: 0.38, h: 0.38, fill: { color: it.color }, line: { color: it.color } });
    s.addText(it.label, { x: 6.85, y,          w: 2.8, h: 0.22, fontSize: 12, fontFace: "Arial Black", color: C.DARK, margin: 0 });
    s.addText(it.note,  { x: 6.85, y: y + 0.22, w: 2.8, h: 0.2,  fontSize: 10, fontFace: "Arial",       color: C.MID,  margin: 0 });
  });

  s.addText("Source: Tabelog Tokyo  ·  Study area: Tokyo 23 wards + surrounds", {
    x: 0.4, y: 5.2, w: 9.2, h: 0.28, fontSize: 9, color: C.MUTED, align: "left",
  });
}

// ── Slide 5: Priority Zones ───────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.NAVY };

  s.addText("Priority Zones", {
    x: 0.5, y: 0.2, w: 9, h: 0.75,
    fontSize: 28, fontFace: "Arial Black", bold: true, color: C.WHITE, margin: 0,
  });
  s.addText("50 shortlisted sites spread across three geographic corridors", {
    x: 0.5, y: 0.9, w: 9, h: 0.4,
    fontSize: 14, fontFace: "Arial", color: C.GOLD, margin: 0,
  });

  const zones = [
    { label: "West Tokyo",  n: "25", sub: "Setagaya · Suginami\nNerima corridors",    col: C.RED  },
    { label: "East Tokyo",  n: "12", sub: "Koto · Sumida\nEdogawa districts",         col: C.GOLD },
    { label: "Central",     n: "11", sub: "Shibuya · Shinjuku\nMinato wards",         col: C.WHITE },
  ];

  zones.forEach((z, i) => {
    const x = 0.7 + i * 3.1, y = 1.7, w = 2.7, h = 3.2;
    const textCol = z.col;
    s.addShape(pres.shapes.RECTANGLE, {
      x, y, w, h, fill: { color: "FFFFFF", transparency: 93 }, line: { color: z.col, width: 2 }, shadow: mkShadow(),
    });
    s.addText(z.n, {
      x, y: y + 0.25, w, h: 1.35,
      fontSize: 80, fontFace: "Arial Black", bold: true, color: textCol, align: "center", margin: 0,
    });
    s.addText("sites", {
      x, y: y + 1.55, w, h: 0.35,
      fontSize: 14, fontFace: "Arial", color: textCol, align: "center", margin: 0,
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: x + 0.65, y: y + 1.95, w: w - 1.3, h: 0.04,
      fill: { color: z.col }, line: { color: z.col },
    });
    s.addText(z.label, {
      x, y: y + 2.1, w, h: 0.4,
      fontSize: 15, fontFace: "Arial Black", bold: true, color: textCol, align: "center", margin: 0,
    });
    s.addText(z.sub, {
      x, y: y + 2.55, w, h: 0.55,
      fontSize: 10, fontFace: "Arial", color: textCol, align: "center", margin: 0,
    });
  });
}

// ── Slide 6: Untapped Markets ─────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.WHITE };

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.85, fill: { color: C.RED }, line: { color: C.RED } });
  s.addText("Untapped Markets — 0 % McDonald's Penetration", {
    x: 0.4, y: 0, w: 9.2, h: 0.85,
    fontSize: 20, fontFace: "Arial Black", bold: true, color: C.WHITE, align: "left", valign: "middle", margin: 0,
  });

  s.addText("These 4 demand zones have strong dining activity but no McDonald's — the highest-priority entry opportunities.", {
    x: 0.5, y: 0.95, w: 9, h: 0.45,
    fontSize: 12, fontFace: "Arial", color: C.MID, margin: 0,
  });

  const zones = [
    { id: "Demand Zone 77", demand: "535 total reviews", n: "17 restaurants", note: "Active dining hub, zero McDonald's presence" },
    { id: "Demand Zone 81", demand: "550 total reviews", n: "10 restaurants", note: "Dense residential + office area"              },
    { id: "Demand Zone 80", demand: "500 total reviews", n: "9 restaurants",  note: "Growing commercial corridor"                 },
    { id: "Demand Zone 73", demand: "347 total reviews", n: "7 restaurants",  note: "Emerging neighbourhood demand"               },
  ];

  zones.forEach((z, i) => {
    const x = i % 2 === 0 ? 0.45 : 5.25;
    const y = 1.6 + Math.floor(i / 2) * 1.75;
    const w = 4.35, h = 1.55;
    s.addShape(pres.shapes.RECTANGLE, { x, y, w, h, fill: { color: C.GRAY }, line: { color: C.LIGHT }, shadow: mkShadow() });
    s.addShape(pres.shapes.RECTANGLE, { x, y, w: 0.07, h, fill: { color: C.GOLD }, line: { color: C.GOLD } });

    s.addText(z.id, {
      x: x + 0.2, y: y + 0.1, w: 1.6, h: 0.35,
      fontSize: 13, fontFace: "Arial Black", bold: true, color: C.RED, margin: 0,
    });
    s.addShape(pres.shapes.RECTANGLE, { x: x + 0.2, y: y + 0.52, w: 1.5, h: 0.28, fill: { color: C.GOLD }, line: { color: C.GOLD } });
    s.addText("100% GAP", {
      x: x + 0.2, y: y + 0.52, w: 1.5, h: 0.28,
      fontSize: 9, fontFace: "Arial Black", bold: true, color: C.NAVY, align: "center", margin: 0,
    });

    s.addText(z.note,   { x: x + 1.9, y: y + 0.1,  w: 2.25, h: 0.35, fontSize: 11, fontFace: "Arial Black", color: C.DARK, margin: 0 });
    s.addText(z.demand, { x: x + 1.9, y: y + 0.55, w: 2.25, h: 0.28, fontSize: 10, fontFace: "Arial",       color: C.MID,  margin: 0 });
    s.addText(z.n,      { x: x + 1.9, y: y + 0.88, w: 2.25, h: 0.28, fontSize: 10, fontFace: "Arial",       color: "E53935", italic: true, margin: 0 });
  });
}

// ── Slide 7: Next Steps ───────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.NAVY };

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0,     w: 10, h: 0.15, fill: { color: C.GOLD }, line: { color: C.GOLD } });
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 5.475, w: 10, h: 0.15, fill: { color: C.GOLD }, line: { color: C.GOLD } });

  s.addText("Recommended Next Steps", {
    x: 0.5, y: 0.35, w: 9, h: 0.75,
    fontSize: 28, fontFace: "Arial Black", bold: true, color: C.WHITE, margin: 0,
  });

  const steps = [
    { n: "01", title: "Site Validation",     body: "Field-survey the top 10 candidates. Confirm foot traffic, street visibility, and property availability." },
    { n: "02", title: "Lease Negotiations",  body: "Engage real estate partners for the 4 zero-gap zones. Prioritise Demand Zones 77 and 81." },
    { n: "03", title: "Demand Verification", body: "Commission daytime population data for office-dense areas to confirm latent demand estimates." },
    { n: "04", title: "Phased Rollout",      body: "Open 3–5 pilot locations in top-scoring West Tokyo sites before committing to the full 50-site programme." },
  ];

  steps.forEach((st, i) => {
    const x = 0.5 + (i % 2) * 4.75, y = 1.35 + Math.floor(i / 2) * 1.8, w = 4.3, h = 1.6;
    s.addShape(pres.shapes.RECTANGLE, {
      x, y, w, h,
      fill: { color: "FFFFFF", transparency: 92 }, line: { color: "FFFFFF", transparency: 70 }, shadow: mkShadow(),
    });

    s.addShape(pres.shapes.OVAL, { x: x + 0.18, y: y + 0.38, w: 0.56, h: 0.56, fill: { color: C.GOLD }, line: { color: C.GOLD } });
    s.addText(st.n, {
      x: x + 0.18, y: y + 0.38, w: 0.56, h: 0.56,
      fontSize: 11, fontFace: "Arial Black", bold: true, color: C.NAVY, align: "center", valign: "middle", margin: 0,
    });

    s.addText(st.title, {
      x: x + 0.9, y: y + 0.15, w: w - 1.05, h: 0.42,
      fontSize: 13, fontFace: "Arial Black", bold: true, color: C.WHITE, margin: 0,
    });
    s.addText(st.body, {
      x: x + 0.9, y: y + 0.6, w: w - 1.05, h: 0.9,
      fontSize: 10.5, fontFace: "Arial", color: "CCCCCC", margin: 0,
    });
  });
}

pres.writeFile({ fileName: "output/business_deck.pptx" })
  .then(() => console.log("✓  output/business_deck.pptx"));
