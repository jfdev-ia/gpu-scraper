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


if __name__ == "__main__":
    # Milestone 12: valid data creates an object, invalid data raises an error
    good = Product(name="Test card", price=1999.0, url="/en/product/1",
                   manufacturer="ASUS", category="Graphics card",
                   energy_consumption=None, image=None)
    print("valid:", good)
    try:
        Product(name="Test card", price="abc", url="/en/product/1",
                manufacturer=None, category=None, energy_consumption=None, image=None)
    except ValidationError as error:
        print("invalid data rejected:", error.errors()[0]["msg"])
    print(Product.model_json_schema())