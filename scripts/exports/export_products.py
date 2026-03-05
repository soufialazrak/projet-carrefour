import os
import pandas as pd

PROJECT_DIR = r"C:\Users\soufi\Documents\projet-carrefour"
DATA_DIR = os.path.join(PROJECT_DIR, "data")

IN_PRODUCTS = os.path.join(DATA_DIR, "products_clean.csv")

OUT_DIR = os.path.join(DATA_DIR, "outputs")
os.makedirs(OUT_DIR, exist_ok=True)

OUT_FILE = os.path.join(OUT_DIR, "products.csv")


def main():
    print("Script export_products démarré...")

    products = pd.read_csv(IN_PRODUCTS)

    required_cols = {
        "product_id",
        "product_category_name",
        "product_weight_g",
        "product_length_cm",
        "product_height_cm",
        "product_width_cm",
    }
    missing = required_cols - set(products.columns)
    if missing:
        raise ValueError(f"Missing columns in products_clean: {missing}")

    out = (
        products[list(required_cols)]
        .drop_duplicates(subset=["product_id"])
        .copy()
    )

    if out["product_id"].isna().any():
        raise ValueError("Null product_id found")
    if out["product_id"].duplicated().any():
        raise ValueError("Duplicate product_id found")

    out.to_csv(OUT_FILE, index=False)
    print(f"[OK] Exported {len(out):,} rows -> {OUT_FILE}")


if __name__ == "__main__":
    main()