### Milestone 3: Inspect the search results

Search URL page: https://www.digitec.ch/en/search?q=RTX%205090

Total number of results: 966

Number of `<atricle>` on first load: 51 (search result mentioning: 48 of 966 products).
3 additional `<atricle>` tags: 3 users comments.
If we scroll to the bottom of the page: 5 Recently viewed articles are displayed
Real articles are in a section with a span(id="product-list").

Product name not included in the raw page source.

### Milestone 4: Locate each field

| Field              | Tag           | How to find it (class, attribute or position) | Example value                                                                                                                      |
| ------------------ | ------------- | --------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| Product name       | a             | position, attribute                           | aria-label="Asus ROG ASTRAL GeForce RTX 5090 OC"                                                                                   |
| Category           | a             | position                                      | Graphics card                                                                                                                      |
| Currency           | div>span>span | position                                      | CHF                                                                                                                                |
| Price              | div>span      | poition                                       | 4018.– was 4233.– (-5%)                                                                                                            |
| Product URL        | a             | position                                      | href="/en/s1/product/asus-rog-astral-geforce-rtx-5090-oc-32-gb-gddr7-graphics-card-54237902"                                       |
| Manufacturer       | p             | position                                      | ASUS (first word of the name)                                                                                                      |
| Energy consumption | N/A           | N/A                                           | N/A                                                                                                                                |
| Image              | picture       | position                                      | src="https://static01.galaxus.com/productimages/2/5/4/6/7/6/9/4/2/9/7/2/6/0/3/1/6/9/01a0b5d3-a8f8-7002-82b3-3e314cdad524_720.jpeg" |
| Availability       | svg           | attribute                                     | aria-label="available in a few weeks"                                                                                              |

**Class names**

- Machine-generated (`yyfb861`, `yWftDNP7`, `ywmBixo3`), so not reliable. Prefer `aria-label`, `id="product-list"` and position.

**Positions (without classes)**

- Name and URL: the first `<a>` in the article. `aria-label` = full name with specs, `href` = relative URL.
- Price: a `<span>` inside a `<div>`. The currency "CHF" is a `<span>` nested inside the price `<span>`.
- Manufacturer: in the name `<p>`, in front of the `<span>`. The `<span>` holds the model name only.
- Category: an `<a>` with the text "Graphics card".
- Image: the `<img>` inside `<picture>`, attribute `src`. No lazy loading.
- Availability: the first `<svg>` with an `aria-label` in the article.

**Availability wordings** (48 products, 2026-10-06)

| `aria-label`             | Count |
| ------------------------ | ----- |
| available                | 19    |
| available in a few days  | 6     |
| available in a few weeks | 21    |
| Availability unknown     | 2     |

- No product says "unavailable". Milestone 16 must map these four wordings to two values.
- Sample for `article_unavailable.html`: "Gigabyte AORUS GeForce RTX 5090 Xtreme Waterforce (32 GB, GDDR7)" (Availability unknown).

**What differs between articles**

- Price: some cards show `current was old (-x%)`.
- Article count: 48 products + 3 magazine posts, + 4 "recently viewed" when the browser has history.
- Energy consumption: not shown on the search page. The parser returns `None`.

**Warning for Milestone 20**
Availability exists only as the `aria-label` of an `<svg>`. Keep the label text before removing the icons.

### Milestone 5: Fetch the page with a script
