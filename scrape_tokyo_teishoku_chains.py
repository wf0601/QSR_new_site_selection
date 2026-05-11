from config import DEFAULT_TEISHOKU_CHAINS
from scraper import run_category_scrape


def main() -> None:
    run_category_scrape(
        category_description="teishoku chains",
        default_brands=DEFAULT_TEISHOKU_CHAINS,
        combined_output_stem="tokyo_teishoku_chains",
    )


if __name__ == "__main__":
    main()
