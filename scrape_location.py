import argparse

from scraper import TabelogScraper, output_paths, save_csv, save_json


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scrape Tabelog restaurants for one chain brand in one Tokyo ward."
    )
    parser.add_argument("brand", help="Brand name, e.g. mcdonalds or マクドナルド")
    parser.add_argument("location", help="Tokyo ward, e.g. shinagawa-ku or C13109")
    parser.add_argument("--max-pages", type=int, default=None, help="Maximum result pages to fetch")
    parser.add_argument("--delay", type=float, default=None, help="Seconds to wait between pages")
    parser.add_argument("--output-dir", default=None, help="Directory for output files")
    parser.add_argument("--csv", default=None, help="CSV output path")
    parser.add_argument("--json", default=None, help="JSON output path")
    parser.add_argument(
        "--no-coordinates",
        action="store_true",
        help="Skip detail-page requests for latitude and longitude",
    )
    args = parser.parse_args()

    scraper = TabelogScraper(
        max_pages=args.max_pages,
        request_delay=args.delay,
        include_coordinates=not args.no_coordinates,
    )
    restaurants = scraper.scrape_brand_location(args.brand, args.location)

    default_csv_path, default_json_path = output_paths(args.brand, args.location, args.output_dir)
    csv_path = args.csv or default_csv_path
    json_path = args.json or default_json_path

    save_csv(restaurants, csv_path)
    save_json(restaurants, json_path)

    print(f"Found {len(restaurants)} restaurants")
    print(f"CSV: {csv_path}")
    print(f"JSON: {json_path}")


if __name__ == "__main__":
    main()
