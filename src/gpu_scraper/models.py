from typing import Literal

from pydantic import BaseModel, Field, ValidationError


class Product(BaseModel):
    name: str = Field(
        description="Full product name with manufacturer and specs, "
        "taken from the aria-label of the first link."
    )
    price: float | None = Field(
        description="Current price in CHF as a plain number, for example 5232.0. "
        "Ignore the old price that follows the word 'was'. null if no price is shown."
    )
    url: str = Field(
        description="The href of the product link, exactly as written in the HTML."
    )
    manufacturer: str | None = Field(
        description="Brand of the product, for example ASUS. null if not in the HTML."
    )
    category: str | None = Field(
        description="Product type shown on the card, for example Graphics card. "
        "null if not in the HTML."
    )
    energy_consumption: str | None = Field(
        description="Power consumption in watts if the HTML states it, "
        "for example '575 W'. null if not in the HTML."
    )
    image: str | None = Field(
        description="The src attribute of the product image. null if there is none."
    )
    availability: Literal["available", "unavailable"] = Field(
        description="Read the aria-label of the availability icon (an svg). "
        "'available' if the label starts with 'available', which includes "
        "'available in a few days' and 'available in a few weeks'. "
        "'unavailable' if the label is 'Availability unknown' or if there is no such label."
    )


if __name__ == "__main__":
    example = dict(name="Test card", price=1999.0, url="/en/product/1",
                   manufacturer="ASUS", category="Graphics card",
                   energy_consumption=None, image=None, availability="available")
    print("valid:", Product(**example))
    
    for field, bad_value in [("price", "abc"), ("availability", "in stock")]:
        try:
            Product(**{**example, field: bad_value})
        except ValidationError as error:
            print(f"{field}={bad_value!r} rejected:", error.errors()[0]["msg"])