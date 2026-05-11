# Geo-intelligence Decision System (Demo)

A data pipeline that scrapes restaurant data from Tabelog, clusters dining-demand zones across Tokyo with HDBSCAN, and scores candidate locations for new McDonald's outlets — complete with an interactive map and PowerPoint decks.

![Interactive map preview](output/screenshot_interactive_map.png)

---

## How it works

```
Tabelog scraping → demand clustering (HDBSCAN) → candidate scoring → interactive map + deck
```

1. **Scrape** — collect location and review data for McDonald's and competitor chains from Tabelog
2. **Cluster** — fit HDBSCAN on all restaurants weighted by review count to discover natural dining-demand zones
3. **Score** — rank a dense candidate grid by cluster demand, McDonald's gap, and distance buffer
4. **Select** — apply greedy NMS (1.5 km spread) to pick geographically diverse top-50 sites
5. **Output** — interactive Folium map + ranked CSV + PowerPoint summary decks

---

## Project structure

```
├── data/                               # Scraped CSVs — gitignored, re-generate with scrape_*.py
│
├── output/
│   ├── interactive_map.html            # Self-contained interactive map (main deliverable)
│   └── top_candidates.csv             # Ranked candidate sites
│
├── assets/
│   └── thumbnail.png                  # Map preview image
│
├── scraper.py                          # Tabelog scraper + shared scraping loop
├── scrape_location.py                  # Single brand/ward scrape utility
├── scrape_tokyo_burger_chains.py       # Scrape burger competitors
├── scrape_tokyo_teishoku_chains.py     # Scrape teishoku competitors
├── scrape_tokyo_family_chains.py       # Scrape family restaurant competitors
│
├── config.py                           # Scraping config (chains, wards, aliases)
├── config_modeling.py                  # All modelling parameters in one place
├── spatial_features.py                 # BallTree helpers (haversine distances)
│
├── site_selection.py                   # Full pipeline: cluster → score → CSV
├── app_interactive.py                  # Interactive HTML map with live controls
│
├── make_pptx.py                        # Deck generator (python-pptx)
│
├── requirements.txt
└── package.json
```

---

## Setup

```bash
pip install -r requirements.txt
npm install          # installs pptxgenjs for deck generation
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
- Red **M** badge — existing McDonald's outlets
- Badge number = rank · opacity = score

---

## Competitor tiers

| Tier | Chains | Weight |
|---|---|---|
| Burger (direct) | MOS Burger, KFC, Wendy's | 1.0 |
| Teishoku (indirect) | Matsuya, Yoshinoya, Sukiya, Nakau, Ootoya | 0.5 |
| Family (indirect) | Gusto, Saizeriya | 0.3 |

Weights set the default demand-signal contribution per category and are live-adjustable in the map.

---

## Scoring formula

```
base_score  = 0.40 × cluster_demand + 0.40 × mcd_gap + 0.20 × distance_buffer
final_score = base_score × membership_strength   (normalised to [0, 1])
```

| Component | Description |
|---|---|
| `cluster_demand` | Total review-weighted demand in the candidate's demand zone |
| `mcd_gap` | Fraction of restaurants in the zone that are *not* McDonald's |
| `distance_buffer` | Safe spacing from the nearest existing outlet (capped at 2 km) |
| `membership_strength` | HDBSCAN soft-cluster confidence (adjustable for sparse areas) |

---

## Key parameters (`config_modeling.py`)

| Parameter | Default | Effect |
|---|---|---|
| `HDBSCAN_PARAMS.min_cluster_size` | 15 | Minimum restaurants to form a demand cluster |
| `MIN_DIST_TO_OWN_KM` | 0.8 km | Cannibalization guard |
| `MAX_DIST_TO_COMP_KM` | 3.0 km | Must be near some market activity |
| `MIN_SPREAD_KM` | 1.5 km | Minimum distance between any two selected sites |
| `TOP_N_SITES` | 50 | Number of candidate sites to output |
| `GRID_STEP_DEG` | 0.003° (~330 m) | Candidate grid resolution |
