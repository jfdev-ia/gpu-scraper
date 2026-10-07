import argparse
import json
import os
import re
import time
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from dotenv import load_dotenv
from mistralai.client import Mistral

from gpu_scraper.clean import strip_images
from gpu_scraper.models import Product

BASE_URL = "https://www.digitec.ch"
MISTRAL_MODEL = "mistral-small-latest"

SYSTEM_PROMPT = """You extract product data from the HTML of one product card of an online shop.
Rules:
- Use only values that are present in the HTML. Never invent a value.
- If a field is not in the HTML, return null for it.
- Copy URLs exactly as they are written in the HTML.
- The price is the current price as a plain number, without currency."""

load_dotenv()


def call_llm(html: str, provider: str = "mistral", model: str = MISTRAL_MODEL) -> tuple[Product, int]:
    """Send one article to the LLM. Return the product and the number of input tokens."""
    if provider != "mistral":
        raise ValueError(f"Unknown provider: {provider}")  # Ollama is added later
    client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])
    response = client.chat.parse(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": html},
        ],
        response_format=Product,
        temperature=0,
    )
    product = response.choices[0].message.parsed
    # Clean in Python what should not be left to the model
    product.name = product.name.replace("\xa0", " ")
    product.url = urljoin(BASE_URL, product.url)
    return product, response.usage.prompt_tokens


def extract_article(html: str, provider: str = "mistral", model: str = MISTRAL_MODEL,
                    clean: bool = False) -> Product:
    """clean=True removes pictures and icons before the call (smaller, faster)."""
    if not clean:
        return call_llm(html, provider, model)[0]
    image = BeautifulSoup(html, "lxml").find("img")
    product, _ = call_llm(strip_images(html), provider, model)
    product.image = image.get("src") if image else None  # the LLM no longer sees it
    return product


def split_articles(html: str) -> list[str]:
    """Return the HTML of every product card (comments and posts are skipped)."""
    soup = BeautifulSoup(html, "lxml")
    articles = soup.find_all("article")
    return [str(a) for a in articles if a.find("a", href=re.compile("/product/"))]


def extract_page(html: str, limit: int | None = None, clean: bool = False) -> list[dict]:
    products, seconds = [], []
    articles = split_articles(html)[:limit]
    for number, article_html in enumerate(articles, start=1):
        start = time.perf_counter()
        try:
            product = extract_article(article_html, clean=clean)
        except Exception as error:  # one failure must not stop the run
            print(f"{number}/{len(articles)} FAILED: {error}")
            time.sleep(5)
            continue
        seconds.append(time.perf_counter() - start)
        products.append(product.model_dump())
        print(f"{number}/{len(articles)} {seconds[-1]:.1f}s  {product.name}")
        time.sleep(1.5)  # stay inside the API rate limit
    if seconds:
        print(f"average: {sum(seconds) / len(seconds):.1f}s per article")
    return products


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["one", "page"])
    parser.add_argument("--limit", type=int, default=None, help="only the first N articles")
    parser.add_argument("--clean", action="store_true", help="remove images before the call")
    args = parser.parse_args()

    if args.mode == "one":
        html = Path("data/samples/article.html").read_text(encoding="utf-8")
        start = time.perf_counter()
        product = extract_article(html, clean=args.clean)
        print(f"{time.perf_counter() - start:.1f}s")
        print(product.model_dump_json(indent=2))
    else:
        html = Path("data/samples/search_page.html").read_text(encoding="utf-8")
        products = extract_page(html, limit=args.limit, clean=args.clean)
        Path("data/out").mkdir(parents=True, exist_ok=True)
        text = json.dumps(products, ensure_ascii=False, indent=2)
        Path("data/out/products_llm.json").write_text(text, encoding="utf-8")
        print(f"saved {len(products)} products to data/out/products_llm.json")