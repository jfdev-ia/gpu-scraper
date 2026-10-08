from pathlib import Path

from bs4 import BeautifulSoup
import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

from gpu_scraper.utils.llm_image_processor import process_image

BASE_URL = "https://www.digitec.ch"

CHART = "div:has(div:has(div.recharts-responsive-container))"

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "data" / "out" / "screenshots"

DIAGRAM_PATH_3_MONTHS = "temp/screenshots/diagram_3m.png"
DIAGRAM_PATH_ALL = "temp/screenshots/diagram_all.png"

def absolute_url(href: str) -> str:
    return href if href.startswith("http") else BASE_URL + href

def parse_article_url(article_html: str):
    soup = BeautifulSoup(article_html, "lxml")
    link = soup.select_one("a[href*='/product/']")
    name = " ".join((link.get("aria-label") or link.get_text(" ")).split())
    url = absolute_url(link["href"])
    
    return {"name": name, "url": url}

def get_product_id(name):
    return name.replace(" ", "_")

async def get_price_trend(product):
    headless = False
    launch_args = ["--start-maximized"]
    images: list[str] = []
    path: str = OUT_DIR / get_product_id(product["name"]) / f"product_{get_product_id(product["name"])}"
    async with Stealth().use_async(async_playwright()) as p:
        browser = await p.chromium.launch(headless=headless, args=launch_args)
        page = await browser.new_page(no_viewport=True)

        await page.goto(product["url"], timeout=60_000)
        await page.locator("#priceHistoryBlock").scroll_into_view_if_needed()
        await page.wait_for_timeout(2000)
        await page.locator("#priceHistoryBlock").click()
        await page.wait_for_selector(CHART, timeout=30_000)
        path_3m = f"{path}_3m.png"
        await page.screenshot(path=path_3m, full_page=False)
        images.append(path_3m)
        await page.locator('button[role="tab"]:has-text("All")').click()
        await page.wait_for_timeout(2000)
        path_all = f"{path}.png"
        await page.screenshot(path=path_all, full_page=False)
        images.append(path_all)
        return images



if __name__ == "__main__":
    product = {
        "name": "PNY GeForce RTX 5060 Overclocked Dual Fan (8 GB, GDDR7)",
        "price": 398.0,
        "url": "https://www.digitec.ch/en/s1/product/pny-geforce-rtx-5060-overclocked-dual-fan-8-gb-gddr7-graphics-card-57628913",
        "manufacturer": "PNY",
        "category": "Graphics card",
        "image": "https://static01.galaxus.com/productimages/4/9/7/6/0/2/1/3/3/5/7/5/2/7/4/9/9/9/5/01a0d4e8-b4db-722a-a845-11d544b5018f_720.jpeg",
        "availability": "available"
    }
    images: list[str] = asyncio.run(get_price_trend(product))
    system_prompt = '''
    This image is a diagram of the price trend of an item.
    Extract the information from the image and present it in a useful format.
    '''

    result = process_image(images[0], system_prompt)
    result = process_image(images[1], system_prompt)
    print(result.choices[0].message.content)    

