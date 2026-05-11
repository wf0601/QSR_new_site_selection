from config import DEFAULT_FAMILY_CHAINS
from scraper import run_category_scrape


def main() -> None:
    run_category_scrape(
        category_description="family chains",
        default_brands=DEFAULT_FAMILY_CHAINS,
        combined_output_stem="tokyo_family_chains",
    )


if __name__ == "__main__":
    main()
