[🇯🇵 日本語](README.md) | [🇬🇧 English](README_EN.md)

# Geo-intelligence Decision System (Demo)

A data pipeline that scrapes restaurant data from a crawlable source (e.g. Google Maps or Tabelog), clusters dining-demand zones across Tokyo with HDBSCAN, and scores candidate locations for new **M** outlets — complete with an interactive map.

| Site selection map | HDBSCAN Explorer |
|:---:|:---:|
| ![Site selection map](assets/dashboard.png) | ![HDBSCAN Explorer](assets/hdbscan.png) |

---

## How it works

```
Scraping → demand clustering (HDBSCAN) → candidate scoring → interactive map
```

1. **Scrape** — collect location and review data for **M** and competitor chains
2. **Cluster** — fit HDBSCAN on all restaurants weighted by review count to discover natural dining-demand zones
3. **Score** — rank a dense candidate grid by cluster demand, **M** gap, and distance buffer
4. **Select** — apply greedy NMS (1.5 km spread) to pick geographically diverse top-50 sites
5. **Output** — interactive Folium map + ranked CSV

---

## Project structure

```
├── assets/
│   └── thumbnail.png                  # Map preview image
│
├── output/
│   ├── interactive_map.html           # Self-contained interactive map (main deliverable)
│   └── top_candidates.csv            # Ranked candidate sites
│
├── scraper.py                         # Tabelog scraper + shared scraping loop
├── scrape_location.py                 # Single brand/ward scrape utility
├── scrape_tokyo_burger_chains.py      # Scrape burger competitors
├── scrape_tokyo_teishoku_chains.py    # Scrape teishoku competitors
├── scrape_tokyo_family_chains.py      # Scrape family restaurant competitors
│
├── config.py                          # Scraping config (chains, wards, aliases)
├── config_modeling.py                 # All modelling parameters in one place
├── spatial_features.py                # BallTree helpers (haversine distances)
│
├── site_selection.py                  # Full pipeline: cluster → score → CSV
├── app_interactive.py                 # Interactive HTML map with live controls
│
└── requirements.txt
```

---

## Setup

```bash
pip install -r requirements.txt
```

---

## Usage

### 1 — Scrape data

Each script only scrapes chains not yet present in `data/` — existing brands load from cache automatically.

```bash
python scrape_tokyo_burger_chains.py
python scrape_tokyo_teishoku_chains.py
python scrape_tokyo_family_chains.py
```

To add a new chain, add its slug to the relevant `DEFAULT_*_CHAINS` list in `config.py` (and add an alias to `BRAND_ALIASES` if needed), then re-run the script.

### 2 — Run site selection

```bash
python site_selection.py     # outputs output/top_candidates.csv
python app_interactive.py    # outputs output/interactive_map.html
```

---

## Interactive map

`output/interactive_map.html` is fully self-contained — open in any browser, no server required.

**Controls (top-right layer panel)**
- **Burger / Teishoku / Family weight** — text inputs next to each competitor layer; controls how much that category's restaurant density contributes to the demand score (`0` = ignore, `1.0` = default, `2.0` = double influence)

**Controls (bottom-right panel)**
- **Sparse Area Confidence** — weight for HDBSCAN noise-reassigned candidates (`0` = hidden, `0.5` = default, `1` = equal weight as confirmed clusters)
- **Top Candidates Shown** — display 5–50 ranked sites (default 50)

**Map elements**
- Green badges — candidates from confirmed demand clusters
- Amber badges — candidates from sparse areas with latent demand
- Red **M** badge — existing **M** outlets
- Badge number = rank · opacity = score

---

## Competitor tiers

| Tier | Chains | Weight |
|---|---|---|
| Burger (direct) | MOS Burger, KFC, Wendy's | 1.0 |
| Teishoku (indirect) | Matsuya, Yoshinoya, Sukiya, Nakau, Ootoya | 0.5 |
| Family (indirect) | Gusto, Saizeriya | 0.3 |

---

## Scoring formula

```
base_score  = 0.40 × cluster_demand + 0.40 × mcd_gap + 0.20 × distance_buffer
final_score = base_score × membership_strength   (normalised to [0, 1])
```

| Component | Description |
|---|---|
| `cluster_demand` | Total review-weighted demand in the candidate's demand zone |
| `mcd_gap` | Fraction of restaurants in the zone that are *not* **M** |
| `distance_buffer` | Safe spacing from the nearest existing outlet (capped at 2 km) |
| `membership_strength` | HDBSCAN soft-cluster confidence (adjustable for sparse areas) |

---

## Worked example: how scoring and Sparse Area Confidence interact

This example uses three simplified candidates to show exactly how a score is computed and why raising the confidence slider can cause a confirmed candidate to disappear from the rankings.

### Setup

| | Candidate X | Candidate Y | Candidate Z |
|---|---|---|---|
| Type | Confirmed cluster | **Sparse area** | Confirmed cluster |
| Proximity | isolated | 600 m from Z | 600 m from Y |
| Cluster demand score | 0.70 | 0.90 | 0.30 |
| M-gap score | 1.00 | 1.00 | 1.00 |
| Distance buffer | 1.00 | 1.00 | 0.70 |

### Step 1 — Compute base score

```
base = 0.40 × demand_score + 0.40 × mcd_gap + 0.20 × distance_buffer
```

```
X:  0.40×0.70 + 0.40×1.0 + 0.20×1.0 = 0.28 + 0.40 + 0.20 = 0.88
Y:  0.40×0.90 + 0.40×1.0 + 0.20×1.0 = 0.36 + 0.40 + 0.20 = 0.96
Z:  0.40×0.30 + 0.40×1.0 + 0.20×0.7 = 0.12 + 0.40 + 0.14 = 0.66
```

### Step 2 — Apply membership weight

Confirmed candidates always have membership = 1.0.
Sparse candidates use the slider value.

```
raw = base × membership
```

**At Sparse Area Confidence = 0.5 (default):**

| Candidate | base | membership | raw |
|---|---|---|---|
| X (confirmed) | 0.88 | 1.0 | **0.880** |
| Y (sparse) | 0.96 | 0.5 | **0.480** |
| Z (confirmed) | 0.66 | 1.0 | **0.660** |

**At Sparse Area Confidence = 0.9:**

| Candidate | base | membership | raw |
|---|---|---|---|
| X (confirmed) | 0.88 | 1.0 | **0.880** |
| Y (sparse) | 0.96 | 0.9 | **0.864** |
| Z (confirmed) | 0.66 | 1.0 | **0.660** |

### Step 3 — Normalise so the best candidate scores 1.0

```
score = raw / max(raw across all candidates)
```

**At confidence = 0.5** — global max is 0.880 (X):

| Candidate | raw | score | sorted rank |
|---|---|---|---|
| X | 0.880 | 1.000 | #1 |
| Z | 0.660 | 0.750 | #2 |
| Y | 0.480 | 0.545 | #3 |

**At confidence = 0.9** — global max is still 0.880 (X):

| Candidate | raw | score | sorted rank |
|---|---|---|---|
| X | 0.880 | 1.000 | #1 |
| Y | 0.864 | 0.982 | #2 |
| Z | 0.660 | 0.750 | #3 |

### Step 4 — Greedy NMS selects in score order, skipping anything within 1.5 km

**At confidence = 0.5** (order: X → Z → Y):

1. Pick X ✅
2. Pick Z ✅ — Y is nearby but hasn't been picked yet, so no conflict
3. Reach Y — only 600 m from Z, which is already selected → **Y is skipped**

**At confidence = 0.9** (order: X → Y → Z):

1. Pick X ✅
2. Pick Y ✅ — marks a 1.5 km exclusion zone around it
3. Reach Z — only 600 m from Y → **Z is blocked and disappears from the top 50**

### Key takeaway

Z's own score never changed. Its base is 0.66 at every confidence level. What changed is that Y — a nearby sparse candidate with a stronger underlying signal — got promoted above Z in the queue when the confidence slider increased. Because the selection is greedy and first-come-first-served, that tiny ordering flip is enough to permanently exclude Z, even though Z scored higher than Y did at low confidence.

**The candidate did not get worse. It got unlucky in the queue.**

> Note: the demand zones themselves (HDBSCAN clusters) are fixed at map generation time and do not change when you move any slider. Only the scoring, ranking, and NMS selection respond to the controls.

---

## Mathematical formulation

### Demand weighting

HDBSCAN is fitted on a review-weighted point cloud. Each restaurant $i$ with review count $c_i$ is replicated $r_i$ times before clustering:

$$r_i = \text{clip}\!\left(\text{round}\!\left(\frac{c_i}{Q_{25}}\right),\ 1,\ 10\right)$$

where $Q_{25}$ is the 25th-percentile review count across all restaurants. High-traffic locations therefore exert proportionally more influence on cluster formation.

### Cluster statistics

For cluster $k$ containing restaurants $\mathcal{R}_k$:

$$D_k = \sum_{i \in \mathcal{R}_k} c_i \qquad \text{(total demand)}$$

$$\text{gap}_k = 1 - \frac{\bigl|\{i \in \mathcal{R}_k : i \text{ is } \mathbf{M}\}\bigr|}{|\mathcal{R}_k|} \qquad \text{(M-gap)}$$

### Candidate scoring

For candidate grid point $p$ assigned to cluster $k(p)$:

$$b(p) = \frac{\min\bigl(d_{\text{own}}(p),\ 2\ \text{km}\bigr)}{2\ \text{km}} \qquad \text{(distance buffer)}$$

$$s_{\text{base}}(p) = 0.40 \cdot \frac{D_{k(p)}}{D_{\max}} + 0.40 \cdot \text{gap}_{k(p)} + 0.20 \cdot b(p)$$

$$s(p) = \frac{s_{\text{base}}(p) \cdot m(p)}{\displaystyle\max_{p'}\, s_{\text{base}}(p') \cdot m(p')} \in [0, 1]$$

where $m(p)$ is the HDBSCAN soft-cluster membership strength ($m = 0.5$ for noise-reassigned candidates by default).

### Greedy diversity selection (NMS)

Sites are selected iteratively. Let $S$ be the chosen set, initialised to $\emptyset$:

$$p^* = \arg\max_{p \,\notin\, S,\ d_H(p,s) \geq 1.5\,\text{km},\ \forall s \in S}\ s(p), \qquad S \leftarrow S \cup \{p^*\}$$

Repeat until $|S| = 50$. This ensures no two selected sites are closer than 1.5 km (configurable via `MIN_SPREAD_KM`).

### Haversine distance

All spatial queries use the haversine metric via scikit-learn `BallTree`:

$$d_H(p, q) = 2R \arcsin\!\sqrt{\sin^2\!\frac{\Delta\phi}{2} + \cos\phi_p\cos\phi_q\,\sin^2\!\frac{\Delta\lambda}{2}}$$

| Symbol | Definition |
|---|---|
| R | 6,371 km (Earth's mean radius) |
| φ | Latitude (radians) |
| λ | Longitude (radians) |

---

## Key parameters (`config_modeling.py`)

| Parameter | Default | Effect |
|---|---|---|
| `HDBSCAN_PARAMS.min_cluster_size` | 5 | Minimum restaurants to form a demand cluster |
| `HDBSCAN_PARAMS.min_samples` | 2 | Minimum neighbours for a core point |
| `MIN_DIST_TO_OWN_KM` | 0.8 km | Cannibalization guard |
| `MAX_DIST_TO_COMP_KM` | 3.0 km | Must be near some market activity |
| `MIN_SPREAD_KM` | 1.5 km | Minimum distance between any two selected sites |
| `TOP_N_SITES` | 50 | Number of candidate sites to output |
| `GRID_STEP_DEG` | 0.002° (~220 m) | Candidate grid resolution |
