"""Run the whole pipeline: fetch the search results, extract the RTX 5090 cards, save them."""
import argparse
import time
from datetime import date
from pathlib import Path

from bs4 import BeautifulSoup

from gpu_scraper import fetch
from gpu_scraper.extract_llm import extract_article
from gpu_scraper.parse_bs import keep_rtx_5090_cards, parse_article, parse_page, save_json

ROOT = Path(__file__).resolve().parents[2]  # the project folder, wherever the program is started
RAW_DIR = ROOT / "data" / "raw"
OUT_DIR = ROOT / "data" / "out"
SAMPLE_PAGE = ROOT / "data" / "samples" / "search_page.html"


def get_html(use_saved: bool, max_products: int | None) -> str:
    """Step 1: load all result pages, or reuse the last saved page."""
    if use_saved:
        saved = sorted(RAW_DIR.glob("search_*.html"))
        path = saved[-1] if saved else SAMPLE_PAGE
        print(f"using saved page {path}")
        return path.read_text(encoding="utf-8")
    html = fetch.fetch_all(max_products=max_products)
    path = RAW_DIR / f"search_{date.today()}.html"
    fetch.save_html(html, str(path))
    print(f"page saved to {path}")
    return html


def extract_cards_bs(html: str) -> list[dict]:
    """Steps 2 to 4 with BeautifulSoup only."""
    return keep_rtx_5090_cards(parse_page(html))


def extract_cards_llm(html: str) -> list[dict]:
    """Steps 2 to 4 with the LLM: BeautifulSoup picks the cards, the LLM reads them."""
    selected, seen = [], set()
    for article in BeautifulSoup(html, "lxml").find_all("article"):
        product = parse_article(article)
        if product and keep_rtx_5090_cards([product]) and product["url"] not in seen:
            seen.add(product["url"])
            selected.append(str(article))

    cards = []
    for number, article_html in enumerate(selected, start=1):
        try:
            product = extract_article(article_html, clean=True)
        except Exception as error:  # one failure must not stop the run
            print(f"{number}/{len(selected)} FAILED: {error}")
            time.sleep(5)
            continue
        cards.append(product.model_dump())
        print(f"{number}/{len(selected)} {product.name}")
        time.sleep(1.5)  # stay inside the API rate limit
    return cards


def run(method: str = "bs", use_saved: bool = False, max_products: int | None = None) -> list[dict]:
    html = get_html(use_saved, max_products)
    cards = extract_cards_llm(html) if method == "llm" else extract_cards_bs(html)
    path = OUT_DIR / f"products_{date.today()}.json"
    save_json(cards, str(path))  # step 5
    print(f"{len(cards)} RTX 5090 graphics cards saved to {path}")
    return cards


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--method", choices=["bs", "llm"], default="bs",
                        help="extract with BeautifulSoup (default) or with the LLM")
    parser.add_argument("--no-fetch", action="store_true",
                        help="reuse the last saved page instead of loading the site")
    parser.add_argument("--max", type=int, default=None, help="load at most N products")
    parser.add_argument("--headless", action="store_true", help="hide the browser window")
    args = parser.parse_args()

    fetch.HEADLESS = args.headless
    run(method=args.method, use_saved=args.no_fetch, max_products=args.max)