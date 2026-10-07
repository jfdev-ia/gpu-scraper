import json
import re
from collections import Counter
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup

BASE_URL = "https://www.digitec.ch"

# Classes copied from data/samples/article.html.
# They are machine-generated and change when digitec rebuilds its site.
NAME_LINK_CLASS = "yyfb861"
PRICE_CLASS = "yRGTUHk1"


def parse_price(text: str) -> float | None:
    """Return the first number in the text: 'CHF4018.– was 4233.–' -> 4018.0"""
    cleaned = text.replace("'", "").replace("’", "")
    match = re.search(r"\d+(?:\.\d+)?", cleaned)
    return float(match.group()) if match else None


def build_product(link, price) -> dict:
    return {
        "name": link["aria-label"].replace("\xa0", " ") if link else None,
        "price": parse_price(price.get_text()) if price else None,
        "url": urljoin(BASE_URL, link["href"]) if link else None,
    }


def parse_article_by_class(article) -> dict:
    link = article.find("a", class_=NAME_LINK_CLASS)
    price = article.find(class_=PRICE_CLASS)
    return build_product(link, price)


def find_price_element(article):
    """Start at the text 'CHF' and walk up to the first element that holds a number."""
    currency = article.find(string=re.compile("CHF"))
    if currency is None:
        return None
    for parent in currency.parents:
        if parent is article:
            return None
        if re.search(r"\d", parent.get_text()):
            return parent
    return None


def parse_article_by_position(article) -> dict:
    link = article.find("a", attrs={"aria-label": True})  # first <a> that has a label
    price = find_price_element(article)
    return build_product(link, price)


def find_manufacturer(article) -> str | None:
    """The name <p> looks like <p><strong>ASUS</strong><span>model</span></p>."""
    for p in article.find_all("p"):
        strong = p.find("strong")
        if strong and p.find("span"):
            return strong.get_text(strip=True)
    return None


def find_energy(article) -> str | None:
    """A value in watts, if the card shows one. The search page usually does not."""
    match = re.search(r"\b\d{2,4}\s?W\b", article.get_text(" "))
    return match.group() if match else None


def parse_article(article) -> dict | None:
    """Return one product, or None if the <article> is not a product."""
    link = article.find("a", attrs={"aria-label": True})
    if link is None or "/product/" not in link.get("href", ""):
        return None  # user comments and magazine posts have no product link
    category = article.find("a", href=re.compile("/producttype/"))
    image = article.find("img")
    product = build_product(link, find_price_element(article))
    product["manufacturer"] = find_manufacturer(article)
    product["category"] = category.get_text(strip=True) if category else None
    product["energy_consumption"] = find_energy(article)
    product["image"] = image.get("src") if image else None
    product["availability"] = parse_availability(article)
    return product


def parse_page(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    products, seen = [], set()
    for article in soup.find_all("article"):
        product = parse_article(article)
        if product is None or product["url"] in seen:
            continue
        seen.add(product["url"])
        products.append(product)
    return products

def parse_availability(article) -> str:
    """'available' if the shop gives a delivery time, 'unavailable' if it does not."""
    icon = article.find("svg", attrs={"aria-label": True})
    if icon is None:
        print("warning: no availability label found, using 'unavailable'")
        return "unavailable"
    label = icon["aria-label"].strip().lower()
    return "available" if label.startswith("available") else "unavailable"

# The search also returns notebooks, PCs and accessories, keep only cards
def keep_rtx_5090_cards(products: list[dict]) -> list[dict]:
    return [p for p in products if p["category"] == "Graphics card" and "5090" in p["name"]]

def save_json(products: list[dict], path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(products, ensure_ascii=False, indent=2)
    Path(path).write_text(text, encoding="utf-8")


if __name__ == "__main__":
    html = Path("data/samples/search_page.html").read_text(encoding="utf-8")
    products = parse_page(html)

    print("articles in page:", html.count("<article"))
    print("products found:  ", len(products))
    for field in products[0]:
        missing = sum(1 for p in products if p[field] is None)
        print(f"  {field}: {missing} missing")
    print("categories:", dict(Counter(p["category"] for p in products)))

    save_json(products, "data/out/products_bs.json")
    print("saved data/out/products_bs.json")