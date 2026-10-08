"""Run the whole pipeline: fetch the results, extract the RTX 5090 cards, report by email."""
import argparse
import json
import time
from datetime import date
from pathlib import Path

from bs4 import BeautifulSoup

import asyncio

from gpu_scraper import fetch
from gpu_scraper.extract_llm import extract_article
from gpu_scraper.mailer import send_email
from gpu_scraper.parse_bs import keep_graphic_cards, parse_article, parse_page, save_json
from gpu_scraper.report import build_report, build_subject

ROOT = Path(__file__).resolve().parents[2]  # the project folder, wherever the program is started
RAW_DIR = ROOT / "data" / "raw"
OUT_DIR = ROOT / "data" / "out"
SAMPLE_PAGE = ROOT / "data" / "samples" / "search_page.html"
MODEL = ["rtx", "5090"]


def get_html(use_saved: bool, model: list | None, nb_pages: int | None) -> str:
    """Step 1: load all result pages, or reuse the last saved page."""
    if use_saved:
        saved = sorted(RAW_DIR.glob("search_*.html"))
        path = saved[-1] if saved else SAMPLE_PAGE
        print(f"using saved page {path}")
        return path.read_text(encoding="utf-8")
    html = asyncio.run(fetch.fetch_all(model=model, nb_pages=nb_pages))
    path = RAW_DIR / f"search_{date.today()}.html"
    fetch.save_html(html, str(path))
    print(f"page saved to {path}")
    return html


def extract_cards_bs(html: str, model: list) -> list[dict]:
    return keep_graphic_cards(parse_page(html), model)


def extract_cards_llm(html: str, model: list) -> list[dict]:
    selected, seen = [], set()
    for article in BeautifulSoup(html, "lxml").find_all("article"):
        product = parse_article(article)
        if product and keep_graphic_cards([product], model) and product["url"] not in seen:
            seen.add(product["url"])
            selected.append(str(article))

    cards = []
    for number, article_html in enumerate(selected, start=1):
        try:
            product = extract_article(article_html, clean=True)
        except Exception as error:  # one failure must not stop the run
            print(f"{number}/{len(selected)} FAILED: {error}")
            time.sleep(5)
            continue
        cards.append(product.model_dump())
        print(f"{number}/{len(selected)} {product.name}")
        time.sleep(1.5)  # stay inside the API rate limit
    return cards


def load_previous() -> tuple[list[dict] | None, str]:
    """The result of the last run before today, to show what changed."""
    today = f"products_{date.today()}.json"
    older = [f for f in sorted(OUT_DIR.glob("products_[0-9]*.json")) if f.name < today]
    if not older:
        return None, ""
    products = json.loads(older[-1].read_text(encoding="utf-8"))
    return products, older[-1].stem.removeprefix("products_")


def run(method: str = "bs", use_saved: bool = False, model:list[str] | None = None, nb_pages: int | None = 0,
        mail: bool = True) -> list[dict]:
    model = model or MODEL
    html = get_html(use_saved, model, nb_pages)
    cards = extract_cards_llm(html, model) if method == "llm" else extract_cards_bs(html, model)
    path = OUT_DIR / f"products_{date.today()}.json"
    save_json(cards, str(path))  # step 5
    print(f"{len(cards)} {' '.join(model)} graphics cards saved to {path}")

    previous, previous_date = load_previous()
    report = build_report(cards, previous, previous_date)  # step 6
    report_path = OUT_DIR / f"report_{date.today()}.html"
    report_path.write_text(report, encoding="utf-8")
    print(f"report saved to {report_path}")

    if mail:  # step 7
        send_email(build_subject(cards), report)
        print("report sent by email")
    return cards


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-m", "--model", type=str, nargs='+', default=[],
                        help="Model of the graphic card: Space-separated list of keywords")
    parser.add_argument("--method", choices=["bs", "llm"], default="bs",
                        help="extract with BeautifulSoup (default) or with the LLM")
    parser.add_argument("--no-fetch", action="store_true",
                        help="reuse the last saved page instead of loading the site")
    parser.add_argument("--no-mail", action="store_true", help="build the report, send nothing")
    parser.add_argument("-hl", "--headless", action="store_true", help="hide the browser window")
    parser.add_argument("-p", "--pages", type=int, default=0, help="number of pages to fetch")
    args = parser.parse_args()

    fetch.HEADLESS = args.headless
    run(method=args.method, use_saved=args.no_fetch, model=args.model, nb_pages=args.pages, mail=not args.no_mail)