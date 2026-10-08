import argparse
from datetime import date
from pathlib import Path

from urllib.parse import urljoin

from playwright.sync_api import Error as PlaywrightError
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

import asyncio

from gpu_scraper.parse_bs import keep_graphic_cards, parse_page, save_json

BASE_URL = "https://www.digitec.ch"
MODEL = ["rtx", "5090"]
BROWSER = "firefox"
HEADLESS = False      # False = you see the window
FIRST_TAKE = 48       # products on the first page
TAKE_STEP = 60        # the site adds 60 each time: 48 -> 108 -> 168 -> ...
MAX_PAGES = 25        # safety limit
PAUSE_SECONDS = 5     # wait between page loads, to be gentle with the site
RETRY_SECONDS = 30    # wait before the one retry after a failed page load


async def fetch_all(base_url: str  | None = BASE_URL, model: list | None = None, nb_pages: int | None = 0) -> str:
    print("Fetch All --------------------------------------------------")
    model = model or MODEL
    url = urljoin(base_url, f"en/search?q={'+'.join(model)}")
    launch_args = ["--start-maximized"]
    """Load the search page with take = 48, 108, 168 ... until every product is loaded."""
    async with Stealth().use_async(async_playwright()) as p:
        browser = await p.chromium.launch(headless=HEADLESS, args=launch_args)
        page = await browser.new_page(no_viewport=True)
        
        take = FIRST_TAKE
        await page.goto(url, wait_until="domcontentloaded")
        await page.wait_for_selector("article", timeout=30_000)
        await page.wait_for_timeout(3000)
        html = await page.content()
        for _ in range(nb_pages):
            count = await page.locator("article").count()
            print(f"{count} articles on the page")
            take += TAKE_STEP
            await page.wait_for_timeout(3000)
            try:
                await page.goto(f"{url}&take={take}", wait_until="domcontentloaded")
                await page.wait_for_timeout(3000)
                html = await page.content()
            except PlaywrightError as error:
                print(f"take={take} could not be loaded, keeping the previous page:\n{error}")
                break
        await browser.close()
    return html

def save_html(html: str, path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(html, encoding="utf-8")


if __name__ == "__main__":
    print("Fetch main method")
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--model", type=str, nargs='+', default=[],
                        help="Model of the graphic card: Space-separated list of keywords")
    parser.add_argument("-p", "--pages", type=int, default=0, help="number of pages to fetch")
    parser.add_argument("-hl", "--headless", action="store_true", help="hide the browser window")
    args = parser.parse_args()
    
    model = args.model or ['rtx', '5090']
    
    html = asyncio.run(fetch_all(model=args.model, nb_pages=args.pages))
    raw_path = f"data/raw/search_{date.today()}.html"
    save_html(html, raw_path)

    products = parse_page(html)
    cards = keep_graphic_cards(products, model)
    print(f"products parsed: {len(products)}")
    print(f"{' '.join(model)} graphics cards: {len(cards)}")
    save_json(products, "data/out/products_all.json")
    save_json(cards, f"data/out/{''.join(model)}_cards.json")
    print(f"saved {raw_path}, data/out/products_all.json, data/out/{''.join(model)}_cards.json")