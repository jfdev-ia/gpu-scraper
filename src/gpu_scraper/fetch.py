import argparse
from datetime import date
from pathlib import Path

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

from gpu_scraper.parse_bs import keep_rtx_5090_cards, parse_page, save_json

SEARCH_URL = "https://www.digitec.ch/en/search?q=rtx+5090"
BROWSER = "firefox"
HEADLESS = False     # False = you see the window
MAX_CLICKS = 25      # safety limit: 48 + 25 x 60 products
PAUSE_SECONDS = 5    # wait between clicks, to be gentle with the site
RETRY_SECONDS = 30   # wait before the one retry if the page does not open


def open_page(page, url: str) -> None:
    """Open the search page. If the connection fails, wait and try once more."""
    try:
        page.goto(url, wait_until="domcontentloaded")
    except PlaywrightError:
        print(f"the page did not open, trying again in {RETRY_SECONDS} seconds")
        page.wait_for_timeout(RETRY_SECONDS * 1000)
        page.goto(url, wait_until="domcontentloaded")
    page.wait_for_selector("article", timeout=30_000)


def count_articles(page) -> int:
    return page.locator("article").count()


def click_show_more(page) -> bool:
    """Click the site's "Show more" link once. Return True if more products appeared."""
    link = page.get_by_text("Show more", exact=True)
    if link.count() == 0:
        return False  # the link is gone: everything is loaded
    before = count_articles(page)
    link.first.click()
    for _ in range(30):  # wait up to 30 seconds for the new products
        page.wait_for_timeout(1000)
        if count_articles(page) > before:
            return True
    return False


def fetch_all(url: str = SEARCH_URL, max_products: int | None = None) -> str:
    """Open the search page and click "Show more" until every product is loaded."""
    with sync_playwright() as p:
        browser = getattr(p, BROWSER).launch(headless=HEADLESS)
        page = browser.new_page()
        open_page(page, url)
        for _ in range(MAX_CLICKS):
            count = count_articles(page)
            print(f"{count} articles on the page")
            if max_products and count >= max_products:
                break
            page.wait_for_timeout(PAUSE_SECONDS * 1000)
            try:
                if not click_show_more(page):
                    break
            except PlaywrightError as error:
                print(f"stopping here, keeping what is loaded:\n{error}")
                break
        html = page.content()
        browser.close()
    return html


def save_html(html: str, path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(html, encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--max", type=int, default=None, help="stop after about N products")
    args = parser.parse_args()

    html = fetch_all(max_products=args.max)
    raw_path = f"data/raw/search_{date.today()}.html"
    save_html(html, raw_path)

    products = parse_page(html)
    cards = keep_rtx_5090_cards(products)
    print(f"products parsed: {len(products)}")
    print(f"RTX 5090 graphics cards: {len(cards)}")
    save_json(products, "data/out/products_all.json")
    save_json(cards, "data/out/rtx5090_cards.json")
    print(f"saved {raw_path}, data/out/products_all.json, data/out/rtx5090_cards.json")