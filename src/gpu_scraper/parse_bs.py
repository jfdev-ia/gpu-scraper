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


def parse_article_by_class(article) -> dict:
    link = article.find("a", class_=NAME_LINK_CLASS)
    price = article.find(class_=PRICE_CLASS)
    return {
        "name": link["aria-label"].replace("\xa0", " ") if link else None,
        "price": parse_price(price.get_text()) if price else None,
        "url": urljoin(BASE_URL, link["href"]) if link else None,
    }


if __name__ == "__main__":
    html = Path("data/samples/article.html").read_text(encoding="utf-8")
    article = BeautifulSoup(html, "lxml").find("article")
    print(parse_article_by_class(article))