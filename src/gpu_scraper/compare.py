import json
from pathlib import Path


def load(path: str) -> dict[str, dict]:
    products = json.loads(Path(path).read_text(encoding="utf-8"))
    return {product["url"]: product for product in products}


if __name__ == "__main__":
    bs = load("data/out/products_bs.json")
    llm = load("data/out/products_llm.json")
    common = [url for url in bs if url in llm]

    print(f"BeautifulSoup: {len(bs)} products, LLM: {len(llm)} products, in both: {len(common)}")
    print("only in BeautifulSoup:", len(bs) - len(common), "| only in LLM:", len(llm) - len(common))

    fields = [field for field in next(iter(bs.values())) if field != "url"]
    for field in fields:
        different = [url for url in common if bs[url][field] != llm[url][field]]
        print(f"\n{field}: {len(common) - len(different)}/{len(common)} equal")
        for url in different:
            print(f"  BS : {bs[url][field]!r}")
            print(f"  LLM: {llm[url][field]!r}")