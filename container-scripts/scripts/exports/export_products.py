import os
from pathlib import Path

import pandas as pd

EXPORTS_DIR = Path(__file__).resolve().parent
PROJECT_DIR = EXPORTS_DIR.parent.parent
DATA_DIR = Path(os.environ.get("DATA_DIR", PROJECT_DIR / "data"))

IN_PRODUCTS = DATA_DIR / "products_clean.csv"
IN_CATEGORIES = DATA_DIR / "outputs" / "product_categories.csv"

OUT_DIR = DATA_DIR / "outputs"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_PRODUCTS = OUT_DIR / "products.csv"


def main():
    print("Script export_products démarré...")

    products = pd.read_csv(IN_PRODUCTS)
    categories = pd.read_csv(IN_CATEGORIES)

    required_product_cols = {
        "product_id",
        "product_category_name",
        "product_weight_g",
        "product_length_cm",
        "product_height_cm",
        "product_width_cm",
    }
    missing_products = required_product_cols - set(products.columns)
    if missing_products:
        raise ValueError(f"Missing columns in products_clean: {missing_products}")

    required_category_cols = {"category_id", "category_name"}
    missing_categories = required_category_cols - set(categories.columns)
    if missing_categories:
        raise ValueError(f"Missing columns in product_categories.csv: {missing_categories}")

    products["product_category_name"] = products["product_category_name"].fillna("unknown")

    products = products.merge(
        categories,
        left_on="product_category_name",
        right_on="category_name",
        how="left"
    )

    if products["category_id"].isna().any():
        missing_names = products.loc[products["category_id"].isna(), "product_category_name"].drop_duplicates().tolist()
        raise ValueError(f"Unmapped product categories found: {missing_names}")

    out_products = (
        products[[
            "product_id",
            "category_id",
            "product_weight_g",
            "product_length_cm",
            "product_height_cm",
            "product_width_cm",
        ]]
        .drop_duplicates(subset=["product_id"])
        .copy()
    )

    if out_products["product_id"].isna().any():
        raise ValueError("Null product_id found")

    if out_products["product_id"].duplicated().any():
        raise ValueError("Duplicate product_id found")

    out_products.to_csv(OUT_PRODUCTS, index=False)
    print(f"[OK] Exported {len(out_products):,} rows -> {OUT_PRODUCTS}")


if __name__ == "__main__":
    main()