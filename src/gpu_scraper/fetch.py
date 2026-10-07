import argparse
import re
import time
from datetime import date
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from gpu_scraper.parse_bs import keep_rtx_5090_cards, parse_page, save_json

SEARCH_URL = "https://www.digitec.ch/en/search?q=rtx+5090"
BROWSER = "firefox"
HEADLESS = False     # False = you see the window
MAX_ROUNDS = 25      # safety limit for the "Show more" loop
PAUSE_SECONDS = 3    # wait between page loads, to be gentle with the site


def load_page(page, url: str) -> str:
    """Open the URL, wait until the product list stops growing, return the HTML."""
    page.goto(url, wait_until="domcontentloaded")
    page.wait_for_selector("article", timeout=30_000)
    previous = -1
    for _ in range(15):
        count = page.locator("article").count()
        if count == previous:
            break
        previous = count
        page.wait_for_timeout(1000)
    return page.content()


def fetch_html(url: str) -> str:
    """One page only (Milestone 5)."""
    with sync_playwright() as p:
        browser = getattr(p, BROWSER).launch(headless=HEADLESS)
        html = load_page(browser.new_page(), url)
        browser.close()
    return html


# Milestone 18: how the site paginates
# The page shows "48 of 966 products" and a "Show more" link to the same URL
# with take=108. "take" is the number of products the page shows.
def read_counter(html: str) -> tuple[int, int] | None:
    """'48 of 966 products' -> (48, 966)"""
    text = re.sub(r"<!--.*?-->", "", html)
    match = re.search(r">([^<>]*?\d) of (\d[^<>]*?) products<", text)
    if match is None:
        return None
    shown, total = (int(re.sub(r"\D", "", group)) for group in match.groups())
    return shown, total


def find_next_url(html: str, current_url: str) -> str | None:
    """The address behind the 'Show more' link, or None on the last page."""
    link = BeautifulSoup(html, "lxml").find("a", href=re.compile(r"[?&]take=\d+"))
    return urljoin(current_url, link["href"]) if link else None


def with_take(url: str, take: int) -> str:
    """Set the take parameter of a search URL."""
    parts = urlsplit(url)
    query = parse_qs(parts.query)
    query["take"] = [str(take)]
    return urlunsplit(parts._replace(query=urlencode(query, doseq=True)))


# Milestone 19: collect all results
def fetch_all(url: str = SEARCH_URL, max_products: int | None = None) -> str:
    """Return the HTML of the search page with all results loaded."""
    with sync_playwright() as p:
        browser = getattr(p, BROWSER).launch(headless=HEADLESS)
        page = browser.new_page()
        html = load_page(page, url)
        counter = read_counter(html)
        if counter is None:
            print("no result counter found, keeping the first page only")
            browser.close()
            return html

        shown, total = counter
        target = min(total, max_products or total)
        print(f"first page: {shown} of {total} products, target: {target}")

        # First ask for everything in one request, then follow "Show more" if needed
        first_try = with_take(url, target)
        next_url = first_try
        for _ in range(MAX_ROUNDS):
            if shown >= target or next_url is None:
                break
            time.sleep(PAUSE_SECONDS)
            new_html = load_page(page, next_url)
            new_shown = (read_counter(new_html) or (0, 0))[0]
            print(f"loaded {new_shown} of {total}")
            if new_shown > shown:
                html, shown = new_html, new_shown
            elif next_url != first_try:
                print("the list stopped growing")
                break
            next_url = find_next_url(html, url)
        browser.close()
    return html


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
    print(f"site counter: {read_counter(html)}")
    print(f"unique products parsed: {len(products)}")
    print(f"RTX 5090 graphics cards: {len(cards)}")
    save_json(products, "data/out/products_all.json")
    save_json(cards, "data/out/rtx5090_cards.json")
    print(f"saved {raw_path}, data/out/products_all.json, data/out/rtx5090_cards.json")