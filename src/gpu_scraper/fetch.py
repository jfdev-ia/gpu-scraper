from playwright.sync_api import sync_playwright

article = ""
article_unavailable = ""

def fetch_html(url:str) -> str:
  print()
  with sync_playwright() as p:
    browser = p.firefox.launch(headless=False)   # False = you see the window
    page = browser.new_page()
    page.goto(url, wait_until="domcontentloaded")
    page.wait_for_selector("article", timeout=30_000)
    global article
    article = page.locator("article").first.evaluate("el => el.outerHTML")
    global article_unavailable
    article_unavailable = page.locator("article").filter(has=page.locator('svg[aria-label="available in a few weeks"]')).first.evaluate("el => el.outerHTML")
    html: str = page.content()
    browser.close()
    return html

def save_html(html: str, path: str = "data/samples/test.html") -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)

if __name__ == "__main__":
  html = fetch_html("https://www.digitec.ch/en/search?q=rtx+5090")
  print(len(html))
  print(html.count("<article"))
  save_html(html, "data/samples/search_page.html")
  save_html(article, "data/samples/article.html")
  save_html(article_unavailable, "data/samples/article_unavailable.html")
  
