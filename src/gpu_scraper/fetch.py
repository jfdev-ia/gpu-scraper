from playwright.sync_api import sync_playwright


def fetch_html(url:str) -> str:
  print()
  with sync_playwright() as p:
    browser = p.firefox.launch(headless=False)   # False = you see the window
    page = browser.new_page()
    page.goto(url, wait_until="domcontentloaded")
    page.wait_for_selector("article", timeout=30_000)
    html: str = page.content()
    browser.close()
    return html

if __name__ == "__main__":
  html = fetch_html("https://www.digitec.ch/en/search?q=rtx+5090")
  print(len(html))
  print(html.count("<article"))
  
