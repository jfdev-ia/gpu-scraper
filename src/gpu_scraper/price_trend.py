from pathlib import Path
import time
import asyncio

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

from gpu_scraper.models import PriceTrend
from gpu_scraper.utils.llm_image_processor import client, encode_image, process_image

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
    path: str = (
        OUT_DIR
        / get_product_id(product["name"])
        / f"product_{get_product_id(product["name"])}"
    )
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


TREND_PROMPT = """You read two screenshots of a product page of an online shop.
Each screenshot contains a graph of the price of one product over time.
The first screenshot shows the last 3 months, the second one the full price history.
Use only what is visible in the graphs. If a price cannot be read, return null."""

TREND_PROMPT2 = """You read a screenshot of a product page of an online shop.
The screenshot contains a graph of the price of one product over time.
The screenshot shows the full price history.
Use only what is visible in the graphs. If a price cannot be read, return null."""

PAUSE_SECONDS = 5  # wait between two products, to be gentle with the site


def classify_trend(images: list[str]) -> PriceTrend:
    """Send both screenshots (3 months, full history) to the LLM in one call."""
    response = client.chat.parse(
        model="mistral-small-2506",
        messages=[
            {"role": "system", "content": TREND_PROMPT2},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Full price history:"},
                    {"type": "image_url", "image_url": encode_image(images[1])},
                ],
            },
        ],
        response_format=PriceTrend,
        reasoning_effort='high',
        temperature=0.7,
    )
    print("-----------------------------------------------------")
    print(response.choices[0].message.model_dump_json())
    print("-----------------------------------------------------")
    return response.choices[0].message.parsed


def buy_signal(product: dict, trend: PriceTrend | None) -> str:
    """Is now a good moment to buy? Returns 'buy', 'wait' or 'no opinion'.
    not available, no price or no graph      -> no opinion
    price in the lowest 20% of its history   -> buy   (about as cheap as it has been)
    price going down                         -> wait  (it may drop further)
    price in the highest 20% of its history  -> wait  (it has been cheaper)
    anything else                            -> no opinion
    """
    if (trend is None or product["price"] is None or product["availability"] != "available"):
        return "no opinion"
    low, high = trend.lowest_price, trend.highest_price
    position = None  # 0 = lowest price seen, 1 = highest price seen
    if low is not None and high is not None and high > low:
        position = (product["price"] - low) / (high - low)
    if position is not None and position <= 0.2:
        return "buy"
    if trend.trend == "DECREASING":
        return "wait"
    if position is not None and position >= 0.8:
        return "wait"
    return "no opinion"


def add_trends(cards: list[dict], limit: int) -> None:
    """Read the price graph of the cheapest available cards and add trend and signal to them."""
    available = [c for c in cards if c["availability"] == "available" and c["price"] is not None]
    selected = sorted(available, key=lambda c: c["price"])[:limit]
    for number, card in enumerate(selected, start=1):
        try:
            trend = classify_trend(asyncio.run(get_price_trend(card)))
        except Exception as error:  # one failure must not stop the run
            print(f"trend {number}/{len(selected)} FAILED for {card['name']}: {error}")
            trend = None

        card["trend"] = trend.trend if trend else None
        card["history"] = trend.history if trend else None
        card["lowest_seen"] = trend.lowest_price if trend else None
        card["highest_seen"] = trend.highest_price if trend else None
        card["signal"] = buy_signal(card, trend)
        print(f"trend {number}/{len(selected)} {card['trend']}, {card['signal']}: {card['name']}")
        time.sleep(PAUSE_SECONDS)


if __name__ == "__main__":
    product = {
        "name": "PNY GeForce RTX 5060 Overclocked Dual Fan (8 GB, GDDR7)",
        "price": 398.0,
        "url": "https://www.digitec.ch/en/s1/product/pny-geforce-rtx-5060-overclocked-dual-fan-8-gb-gddr7-graphics-card-57628913",
        "manufacturer": "PNY",
        "category": "Graphics card",
        "image": "https://static01.galaxus.com/productimages/4/9/7/6/0/2/1/3/3/5/7/5/2/7/4/9/9/9/5/01a0d4e8-b4db-722a-a845-11d544b5018f_720.jpeg",
        "availability": "available",
    }
    images: list[str] = asyncio.run(get_price_trend(product))
    system_prompt = """
    This image is a diagram of the price trend of an item.
    Extract the information from the image and present it in a useful format.
    """

    result = process_image(images[0], system_prompt)
    result = process_image(images[1], system_prompt)
    print(result.choices[0].message.content)
