from pathlib import Path

from bs4 import BeautifulSoup


def strip_images(article_html: str, keep_labels: bool = True) -> str:
    """Remove pictures and icons from the HTML of one article.

    keep_labels=True keeps an empty <svg aria-label="..."> tag, because the
    availability of a product exists only as the label of an icon.
    """
    soup = BeautifulSoup(article_html, "lxml")
    for picture in soup.find_all("picture"):
        picture.decompose()
    for image in soup.find_all("img"):
        image.decompose()
    for svg in soup.find_all("svg"):
        label = svg.get("aria-label")
        if keep_labels and label:
            svg.clear()  # drop the drawing, keep the label
            svg.attrs = {"aria-label": label}
        else:
            svg.decompose()
    article = soup.find("article")
    return str(article) if article else str(soup)


if __name__ == "__main__":
    html = Path("data/samples/article.html").read_text(encoding="utf-8")
    for keep_labels in (False, True):
        cleaned = strip_images(html, keep_labels=keep_labels)
        print(f"keep_labels={keep_labels}: {len(html)} -> {len(cleaned)} characters")
    print(cleaned)