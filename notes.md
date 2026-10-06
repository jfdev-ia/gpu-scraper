### Milestone 3: Inspect the search results

Search URL page: https://www.digitec.ch/en/search?q=RTX%205090

Total number of results: 930

Number of `<atricle>` on first load: 55 (search result mentioning: 48 of 930 products).
7 additional `<atricle>` tags: 4 Recently viewed - 3 magazine posts.
Real articles are in a section with a span(id="product-list").

Product name not included in the raw page source.

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
