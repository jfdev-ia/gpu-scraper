"""Compare speed and quality of the LLM with and without images in the HTML."""
import argparse
import time
from pathlib import Path

from bs4 import BeautifulSoup

from gpu_scraper.clean import strip_images
from gpu_scraper.extract_llm import call_llm, split_articles
from gpu_scraper.parse_bs import parse_article

VARIANTS = {
    "Raw HTML": lambda html: html,
    "Images removed": lambda html: strip_images(html, keep_labels=False),
    "Images removed, labels kept": lambda html: strip_images(html, keep_labels=True),
}


def measure(articles: list[str]) -> None:
    rows = []
    for variant, prepare in VARIANTS.items():
        chars, tokens, seconds, calls = 0, 0, 0.0, 0
        correct: dict[str, int] = {}
        for number, article_html in enumerate(articles, start=1):
            reference = parse_article(BeautifulSoup(article_html, "lxml").find("article"))
            text = prepare(article_html)
            start = time.perf_counter()
            try:
                product, prompt_tokens = call_llm(text)
            except Exception as error:
                print(f"{variant} {number}/{len(articles)} FAILED: {error}")
                time.sleep(5)
                continue
            seconds += time.perf_counter() - start
            chars, tokens, calls = chars + len(text), tokens + prompt_tokens, calls + 1
            result = product.model_dump()
            for field, expected in reference.items():
                correct[field] = correct.get(field, 0) + (result[field] == expected)
            print(f"{variant} {number}/{len(articles)}")
            time.sleep(1.5)
        if calls:
            rows.append((variant, chars / calls, tokens / calls, seconds / calls, calls, correct))

    fields = list(rows[0][5]) if rows else []
    print("\n| Variant | Avg. characters | Avg. input tokens | Avg. seconds | "
          + " | ".join(fields) + " |")
    print("| --- | --- | --- | --- |" + " --- |" * len(fields))
    for variant, avg_chars, avg_tokens, avg_seconds, calls, correct in rows:
        cells = " | ".join(f"{correct[field]}/{calls}" for field in fields)
        print(f"| {variant} | {avg_chars:.0f} | {avg_tokens:.0f} | {avg_seconds:.1f} | {cells} |")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=10, help="number of articles per variant")
    args = parser.parse_args()
    html = Path("data/samples/search_page.html").read_text(encoding="utf-8")
    measure(split_articles(html)[: args.limit])