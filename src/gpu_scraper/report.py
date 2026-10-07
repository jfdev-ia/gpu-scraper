"""Build the daily price report as an HTML page."""
import html
import statistics
from datetime import datetime


def money(price: float | None) -> str:
    if price is None:
        return "no price"
    text = f"{price:,.0f}" if price == int(price) else f"{price:,.2f}"
    return "CHF " + text.replace(",", "'")


def sort_by_price(products: list[dict]) -> list[dict]:
    """Cheapest first, cards without a price at the end."""
    return sorted(products, key=lambda p: (p["price"] is None, p["price"] or 0))


def available_with_price(products: list[dict]) -> list[dict]:
    return [p for p in products if p["availability"] == "available" and p["price"] is not None]


def find_changes(products: list[dict], previous: list[dict]) -> dict:
    old = {p["url"]: p for p in previous}
    new = {p["url"]: p for p in products}
    return {
        "new": [p for url, p in new.items() if url not in old],
        "removed": [p for url, p in old.items() if url not in new],
        "price": [(p, old[url]["price"]) for url, p in new.items()
                  if url in old and p["price"] != old[url]["price"]],
    }


def link(product: dict) -> str:
    return f'<a href="{html.escape(product["url"])}">{html.escape(product["name"])}</a>'


def changes_section(products: list[dict], previous: list[dict], previous_date: str) -> str:
    changes = find_changes(products, previous)
    items = []
    for product, old_price in changes["price"]:
        line = f"{link(product)}: {money(old_price)} &rarr; {money(product['price'])}"
        if product["price"] is not None and old_price is not None:
            difference = product["price"] - old_price
            colour = "#1a7f37" if difference < 0 else "#b42318"
            amount = f"{difference:+,.0f}".replace(",", "'")
            line += f' <b style="color:{colour}">({amount})</b>'
        items.append(f"<li>{line}</li>")
    items += [f"<li>New: {link(p)} at {money(p['price'])}</li>" for p in changes["new"]]
    items += [f"<li>No longer listed: {link(p)}</li>" for p in changes["removed"]]
    body = f"<ul>{''.join(items)}</ul>" if items else "<p>No change.</p>"
    return f"<h3>Changes since {html.escape(previous_date)}</h3>{body}"


def build_report(products: list[dict], previous: list[dict] | None = None,
                 previous_date: str = "the last run") -> str:
    buyable = available_with_price(products)
    parts = [
        '<div style="font-family:Arial,Helvetica,sans-serif;font-size:14px;color:#1f2328;max-width:820px">',
        f"<h2>RTX 5090 price report, {datetime.now():%d %B %Y, %H:%M}</h2>",
        f"<p>{len(products)} graphics cards found on digitec.ch, "
        f"{sum(p['availability'] == 'available' for p in products)} available.</p>",
    ]
    if buyable:
        cheapest = min(buyable, key=lambda p: p["price"])
        prices = [p["price"] for p in buyable]
        parts.append(f"<p><b>Cheapest available card:</b> {link(cheapest)} at <b>{money(cheapest['price'])}</b></p>")
        parts.append(f"<p>Available cards: lowest {money(min(prices))}, "
                     f"median {money(statistics.median(prices))}, highest {money(max(prices))}.</p>")
    else:
        parts.append("<p><b>No card is available with a price today.</b></p>")

    if previous is not None:
        parts.append(changes_section(products, previous, previous_date))

    cell = 'style="padding:6px 10px;border-bottom:1px solid #d0d7de;text-align:left"'
    right = cell.replace("text-align:left", "text-align:right;white-space:nowrap")
    rows = []
    for product in sort_by_price(products):
        grey = ' style="color:#8c959f"' if product["availability"] != "available" else ""
        rows.append(
            f"<tr{grey}><td {cell}>{link(product)}</td>"
            f"<td {cell}>{html.escape(product['manufacturer'] or '')}</td>"
            f'<td {right}>{money(product["price"])}</td>'
            f"<td {cell}>{html.escape(product['availability'])}</td></tr>"
        )
    parts.append("<h3>All cards by price</h3>")
    parts.append('<table style="border-collapse:collapse;width:100%">'
                 f"<tr><th {cell}>Card</th><th {cell}>Manufacturer</th>"
                 f'<th {right}>Price</th><th {cell}>Availability</th></tr>'
                 + "".join(rows) + "</table></div>")
    return "\n".join(parts)


def build_subject(products: list[dict]) -> str:
    buyable = available_with_price(products)
    if not buyable:
        return f"RTX 5090 prices {datetime.now():%Y-%m-%d}: no card available"
    cheapest = min(p["price"] for p in buyable)
    return f"RTX 5090 prices {datetime.now():%Y-%m-%d}: cheapest available {money(cheapest)}" 