from config import DEFAULT_BURGER_CHAINS
from scraper import run_category_scrape


def main() -> None:
    run_category_scrape(
        category_description="burger chains",
        default_brands=DEFAULT_BURGER_CHAINS,
        combined_output_stem="tokyo_burger_chains",
    )


if __name__ == "__main__":
    main()
