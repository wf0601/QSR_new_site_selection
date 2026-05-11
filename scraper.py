import argparse
import csv
import json
import re
import time
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import parse_qs, urlencode, urlparse

import requests
from bs4 import BeautifulSoup

from config import (
    BRAND_ALIASES,
    BRAND_NAME_PATTERNS,
    OUTPUT_SETTINGS,
    SCRAPE_SETTINGS,
    TOKYO_LOCATIONS,
    TOKYO_WARDS,
    USER_AGENT,
)


@dataclass
class Restaurant:
    name: str
    url: str
    brand: str
    location: str
    ward: str = ""
    score: str = ""
    reviews: str = ""
    budget_dinner: str = ""
    budget_lunch: str = ""
    area: str = ""
    genre: str = ""
    address: str = ""
    latitude: str = ""
    longitude: str = ""
    source_url: str = ""


class TabelogScraper:
    def __init__(
        self,
        request_delay: float | None = None,
        timeout: int | None = None,
        max_pages: int | None = None,
        include_coordinates: bool = True,
    ) -> None:
        self.request_delay = SCRAPE_SETTINGS["request_delay"] if request_delay is None else request_delay
        self.timeout = SCRAPE_SETTINGS["timeout"] if timeout is None else timeout
        self.max_pages = SCRAPE_SETTINGS["max_pages"] if max_pages is None else max_pages
        self.include_coordinates = include_coordinates
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
            }
        )

    def scrape_brand_location(self, brand: str, location: str) -> list[Restaurant]:
        brand_query = normalize_brand(brand)
        location_code = normalize_location(location)
        restaurants: list[Restaurant] = []
        seen_urls: set[str] = set()

        for page in range(1, self.max_pages + 1):
            url = build_search_url(brand_query, location_code, page)
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            page_items = parse_restaurants(response.text, brand_query, location, url)
            for item in page_items:
                dedupe_key = restaurant_dedupe_key(item)
                if (
                    not item.url
                    or dedupe_key in seen_urls
                    or not restaurant_matches_brand(item, brand_query)
                ):
                    continue
                seen_urls.add(dedupe_key)
                restaurants.append(item)

            if not page_items or not has_next_page(response.text):
                break

            time.sleep(self.request_delay)

        if self.include_coordinates:
            self.add_coordinates(restaurants)

        return restaurants

    def add_coordinates(self, restaurants: list[Restaurant]) -> None:
        for index, restaurant in enumerate(restaurants):
            try:
                response = self.session.get(restaurant.url, timeout=self.timeout)
                response.raise_for_status()
                latitude, longitude = extract_coordinates(response.text)
                restaurant.latitude = latitude
                restaurant.longitude = longitude
            except requests.RequestException:
                restaurant.latitude = ""
                restaurant.longitude = ""

            if index < len(restaurants) - 1:
                time.sleep(self.request_delay)


def normalize_brand(brand: str) -> str:
    clean_brand = brand.strip()
    return BRAND_ALIASES.get(clean_brand.lower(), clean_brand)


def normalize_location(location: str) -> str:
    clean_location = location.strip()
    lookup_key = clean_location.lower().replace("_", "-").replace(" ", "-")
    if lookup_key in TOKYO_LOCATIONS:
        return TOKYO_LOCATIONS[lookup_key]
    if re.fullmatch(r"C\d{5}", clean_location, flags=re.IGNORECASE):
        return clean_location.upper()
    raise ValueError(
        f"Unknown Tokyo location '{location}'. Add it to TOKYO_LOCATIONS in config.py "
        "or pass a Tabelog city code such as C13109."
    )


def restaurant_matches_brand(restaurant: Restaurant, brand: str) -> bool:
    patterns = BRAND_NAME_PATTERNS.get(brand, [brand])
    restaurant_name = restaurant.name.casefold()
    return any(pattern.casefold() in restaurant_name for pattern in patterns)


def restaurant_dedupe_key(restaurant: Restaurant) -> str:
    parsed_url = urlparse(restaurant.url)
    clean_path = parsed_url.path.rstrip("/")
    if parsed_url.netloc and clean_path:
        return f"{parsed_url.netloc}{clean_path}"
    return restaurant.name.casefold()


def build_search_url(brand: str, location_code: str, page: int = 1) -> str:
    page_part = "" if page == 1 else f"{page}/"
    params = {
        "sw": brand,
        "sk": brand,
        "svd": date.today().strftime("%Y%m%d"),
        "svt": SCRAPE_SETTINGS["search_time"],
        "svps": SCRAPE_SETTINGS["party_size"],
    }
    return f"https://tabelog.com/tokyo/{location_code}/rstLst/{page_part}?{urlencode(params)}"


def parse_restaurants(html: str, brand: str, location: str, source_url: str) -> list[Restaurant]:
    soup = BeautifulSoup(html, "lxml")
    cards = soup.select(
        "li.list-rst, li.js-rst-cassette-wrap, "
        "div.list-rst__wrap, div.js-open-new-window"
    )
    restaurants: list[Restaurant] = []

    for card in cards:
        name_link = card.select_one(
            "a.list-rst__rst-name-target, a.cpy-rst-name, "
            "a.js-click-rdlog, a[href*='/tokyo/']"
        )
        if not name_link:
            continue

        name = compact_text(name_link.get_text(" ", strip=True))
        url = name_link.get("href", "").strip()
        if not name or not url:
            continue

        restaurants.append(
            Restaurant(
                name=name,
                url=url,
                brand=brand,
                location=location,
                ward=location,
                score=text_or_empty(card.select_one("span.list-rst__rating-val, span.c-rating__val")),
                reviews=text_or_empty(card.select_one("em.list-rst__rvw-count-num, a.list-rst__rvw-count-target")),
                budget_dinner=text_or_empty(card.select_one(".list-rst__budget-item--dinner")),
                budget_lunch=text_or_empty(card.select_one(".list-rst__budget-item--lunch")),
                area=text_or_empty(card.select_one(".list-rst__area-genre .list-rst__area")),
                genre=text_or_empty(card.select_one(".list-rst__area-genre .list-rst__genre")),
                address=text_or_empty(card.select_one(".list-rst__address, .cpy-address")),
                source_url=source_url,
            )
        )

    return restaurants


def has_next_page(html: str) -> bool:
    soup = BeautifulSoup(html, "lxml")
    return soup.select_one("a.c-pagination__target--next, a[rel='next']") is not None


def extract_coordinates(html: str) -> tuple[str, str]:
    soup = BeautifulSoup(html, "lxml")

    for script in soup.select("script[type='application/ld+json']"):
        payload = script.string or script.get_text(strip=True)
        if not payload:
            continue
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            continue

        coordinates = find_geo_coordinates(data)
        if coordinates:
            return coordinates

    lat_match = re.search(r'"latitude"\s*:\s*"?([0-9.]+)"?', html)
    lng_match = re.search(r'"longitude"\s*:\s*"?([0-9.]+)"?', html)
    if lat_match and lng_match:
        return lat_match.group(1), lng_match.group(1)

    print_url = soup.select_one("[data-print-url*='lat='][data-print-url*='lng=']")
    if print_url:
        query = parse_qs(urlparse(print_url.get("data-print-url", "")).query)
        latitude = first_query_value(query, "latitude")
        longitude = first_query_value(query, "lng")
        if latitude and longitude:
            return latitude, longitude

    return "", ""


def find_geo_coordinates(data: Any) -> tuple[str, str] | None:
    if isinstance(data, dict):
        geo = data.get("geo")
        if isinstance(geo, dict) and "latitude" in geo and "longitude" in geo:
            return str(geo["latitude"]), str(geo["longitude"])

        for value in data.values():
            coordinates = find_geo_coordinates(value)
            if coordinates:
                return coordinates

    if isinstance(data, list):
        for item in data:
            coordinates = find_geo_coordinates(item)
            if coordinates:
                return coordinates

    return None


def first_query_value(query: dict[str, list[str]], key: str) -> str:
    values = query.get(key, [])
    return values[0] if values else ""


def text_or_empty(node) -> str:
    if node is None:
        return ""
    return compact_text(node.get_text(" ", strip=True))


def compact_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def save_json(restaurants: Iterable[Restaurant], path: str | Path) -> None:
    rows = [asdict(restaurant) for restaurant in restaurants]
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")


def save_csv(restaurants: Iterable[Restaurant], path: str | Path) -> None:
    rows = [asdict(restaurant) for restaurant in restaurants]
    fieldnames = list(Restaurant.__dataclass_fields__.keys())
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def output_paths(brand: str, location: str, output_dir: str | Path | None = None) -> tuple[Path, Path]:
    stem = f"{slugify(brand)}_{slugify(location)}"
    if output_dir is not None:
        output_dir = Path(output_dir)
        return output_dir / f"{stem}.csv", output_dir / f"{stem}.json"

    return (
        Path(OUTPUT_SETTINGS["csv_file"].format(stem=stem)),
        Path(OUTPUT_SETTINGS["json_file"].format(stem=stem)),
    )


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^0-9a-zA-Zぁ-んァ-ン一-龥ー]+", "_", value)
    return value.strip("_") or "restaurants"


def load_csv(path: str | Path) -> list[Restaurant]:
    """Load a previously-saved CSV back into Restaurant objects."""
    known_fields = set(Restaurant.__dataclass_fields__)
    rows = []
    with Path(path).open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append(Restaurant(**{k: row.get(k, "") for k in known_fields}))
    return rows


def run_category_scrape(
    category_description: str,
    default_brands: list[str],
    combined_output_stem: str,
) -> None:
    """
    Shared scraping loop used by all three category scripts.

    For each brand the function first checks whether
    ``{output_dir}/{brand_slug}_tokyo.csv`` already exists.  If it does the
    brand is loaded from disk and skipped — only brands whose file is absent
    are scraped.  This means adding a new chain to a DEFAULT_* list re-runs
    only that chain; existing chains are untouched.

    The combined output file (e.g. tokyo_burger_chains.csv) is always rebuilt
    from the full set so it stays consistent after each run.
    """
    parser = argparse.ArgumentParser(
        description=f"Scrape selected {category_description} across Tokyo's 23 wards."
    )
    parser.add_argument(
        "--brands",
        nargs="+",
        default=default_brands,
        help="Brand names to scrape.",
    )
    parser.add_argument(
        "--wards",
        nargs="+",
        default=[ward for ward, _code in TOKYO_WARDS],
        help="Ward slugs to scrape, e.g. shinagawa-ku shibuya-ku",
    )
    parser.add_argument("--max-pages", type=int, default=None, help="Maximum result pages per ward")
    parser.add_argument("--delay", type=float, default=None, help="Seconds to wait between requests")
    parser.add_argument(
        "--output-dir",
        default=OUTPUT_SETTINGS["data_dir"],
        help="Directory for per-brand and combined output files",
    )
    parser.add_argument(
        "--no-coordinates",
        action="store_true",
        help="Skip detail-page requests for latitude and longitude",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    ward_slugs = {ward for ward, _code in TOKYO_WARDS}
    unknown_wards = sorted(set(args.wards) - ward_slugs)
    if unknown_wards:
        raise ValueError(f"Unknown wards: {', '.join(unknown_wards)}")

    all_restaurants: list[Restaurant] = []
    failures: list[dict] = []

    for brand in args.brands:
        brand_slug = slugify(brand)
        brand_csv = output_dir / f"{brand_slug}_tokyo.csv"

        if brand_csv.exists():
            cached = load_csv(brand_csv)
            print(
                f"{normalize_brand(brand)}: cached — "
                f"loaded {len(cached)} restaurants from {brand_csv}",
                flush=True,
            )
            all_restaurants.extend(cached)
            continue

        # Brand is new — scrape all requested wards
        print(f"{normalize_brand(brand)}: no cached data, scraping...", flush=True)
        brand_dir = output_dir / brand_slug
        brand_dir.mkdir(parents=True, exist_ok=True)
        brand_restaurants: list[Restaurant] = []

        for ward, _code in TOKYO_WARDS:
            if ward not in args.wards:
                continue

            print(f"  {ward}...", flush=True)
            scraper = TabelogScraper(
                max_pages=args.max_pages,
                request_delay=args.delay,
                include_coordinates=not args.no_coordinates,
            )

            try:
                restaurants = scraper.scrape_brand_location(brand, ward)
            except Exception as exc:
                failures.append({"brand": brand, "ward": ward, "error": str(exc)})
                print(f"    failed: {exc}", flush=True)
                continue

            ward_slug = slugify(ward)
            save_csv(restaurants, brand_dir / f"{brand_slug}_{ward_slug}.csv")
            save_json(restaurants, brand_dir / f"{brand_slug}_{ward_slug}.json")

            brand_restaurants.extend(restaurants)
            all_restaurants.extend(restaurants)
            print(f"    found {len(restaurants)} restaurants", flush=True)

        save_csv(brand_restaurants, brand_csv)
        save_json(brand_restaurants, output_dir / f"{brand_slug}_tokyo.json")
        print(
            f"{normalize_brand(brand)}: done — {len(brand_restaurants)} restaurants saved",
            flush=True,
        )

    # Rebuild combined file from cached + newly scraped brands
    save_csv(all_restaurants, output_dir / f"{combined_output_stem}.csv")
    save_json(all_restaurants, output_dir / f"{combined_output_stem}.json")

    if failures:
        failures_path = output_dir / "failures.json"
        failures_path.write_text(
            json.dumps(failures, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"Failures: {len(failures)} written to {failures_path}", flush=True)

    print(f"\nTotal restaurants: {len(all_restaurants)}", flush=True)
    print(f"Output directory:  {output_dir}", flush=True)
    print("Brands:            " + ", ".join(normalize_brand(b) for b in args.brands), flush=True)
