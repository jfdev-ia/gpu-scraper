import re
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


# Milestone 7: find the elements by class
def parse_article_by_class(article) -> dict:
    link = article.find("a", class_=NAME_LINK_CLASS)
    price = article.find(class_=PRICE_CLASS)
    return build_product(link, price)


# Milestone 8: find the elements by position, no class names
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


if __name__ == "__main__":
    for name in ["article.html", "article_unavailable.html"]:
        html = Path("data/samples", name).read_text(encoding="utf-8")
        article = BeautifulSoup(html, "lxml").find("article")
        by_class = parse_article_by_class(article)
        by_position = parse_article_by_position(article)
        print(name)
        print("  class:   ", by_class)
        print("  position:", by_position)
        print("  identical:", by_class == by_position)