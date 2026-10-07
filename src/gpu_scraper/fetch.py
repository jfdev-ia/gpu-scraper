import argparse
import re
from datetime import date
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

from gpu_scraper.parse_bs import keep_rtx_5090_cards, parse_page, save_json

SEARCH_URL = "https://www.digitec.ch/en/search?q=rtx+5090"
BROWSER = "firefox"
HEADLESS = False     # False = you see the window
MAX_PAGES = 25       # safety limit
PAUSE_SECONDS = 5    # wait between page loads, to be gentle with the site
RETRY_SECONDS = 30   # wait before the one retry after a failed page load


def load_page(page, url: str) -> str:
    """Open the URL and return the HTML. A failed load is tried once more."""
    try:
        page.goto(url, wait_until="domcontentloaded")
    except PlaywrightError as error:
        print(f"page load failed ({str(error).splitlines()[0]}), retrying in {RETRY_SECONDS}s")
        page.wait_for_timeout(RETRY_SECONDS * 1000)
        page.goto(url, wait_until="domcontentloaded")
    page.wait_for_selector("article", timeout=30_000)
    page.wait_for_timeout(2000)  # let the list finish drawing
    return page.content()


def find_next_url(html: str, current_url: str) -> str | None:
    """The address behind the site's "Show more" link, or None on the last page.

    The link points to the same search with a take parameter (48 -> 108 -> 168 ...).
    """
    link = BeautifulSoup(html, "lxml").find("a", href=re.compile(r"[?&]take=\d+"))
    return urljoin(current_url, link["href"]) if link else None


def load_more(page, html: str, url: str) -> str | None:
    """Follow the "Show more" link once. Return the new HTML, or None if there is no more."""
    next_url = find_next_url(html, url)
    if next_url is None:
        return None  # this was the last page
    page.wait_for_timeout(PAUSE_SECONDS * 1000)
    try:
        new_html = load_page(page, next_url)
    except PlaywrightError as error:
        print(f"stopping here: {str(error).splitlines()[0]}")
        return None  # keep the pages that did load
    if len(parse_page(new_html)) <= len(parse_page(html)):
        return None  # the site sent nothing new
    return new_html


def fetch_all(url: str = SEARCH_URL, max_products: int | None = None) -> str:
    """Load the search page, then follow "Show more" until every product is loaded."""
    with sync_playwright() as p:
        browser = getattr(p, BROWSER).launch(headless=HEADLESS)
        page = browser.new_page()
        html = load_page(page, url)
        for _ in range(MAX_PAGES):
            count = len(parse_page(html))
            print(f"{count} products loaded")
            if max_products and count >= max_products:
                break
            bigger = load_more(page, html, url)
            if bigger is None:
                break
            html = bigger
        browser.close()
    return html


def read_counter(html: str) -> tuple[int, int] | None:
    """The site's own counter: '48 of 966 products' -> (48, 966)"""
    text = re.sub(r"<!--.*?-->", "", html)
    match = re.search(r">([^<>]*?\d) of (\d[^<>]*?) products<", text)
    if match is None:
        return None
    shown, total = (int(re.sub(r"\D", "", group)) for group in match.groups())
    return shown, total


def save_html(html: str, path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(html, encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--max", type=int, default=None, help="stop after N products")
    args = parser.parse_args()

    html = fetch_all(max_products=args.max)
    raw_path = f"data/raw/search_{date.today()}.html"
    save_html(html, raw_path)

    products = parse_page(html)
    cards = keep_rtx_5090_cards(products)
    print(f"site counter (shown, total): {read_counter(html)}")
    print(f"unique products parsed: {len(products)}")
    print(f"RTX 5090 graphics cards: {len(cards)}")
    save_json(products, "data/out/products_all.json")
    save_json(cards, "data/out/rtx5090_cards.json")
    print(f"saved {raw_path}, data/out/products_all.json, data/out/rtx5090_cards.json")