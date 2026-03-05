import os
import pandas as pd

PROJECT_DIR = r"C:\Users\soufi\Documents\projet-carrefour"
DATA_DIR = os.path.join(PROJECT_DIR, "data")

IN_PRODUCTS = os.path.join(DATA_DIR, "products_clean.csv")

OUT_DIR = os.path.join(DATA_DIR, "outputs")
os.makedirs(OUT_DIR, exist_ok=True)

OUT_FILE = os.path.join(OUT_DIR, "product_categories.csv")


def main():
    print("Script export_product_categories démarré...")

    products = pd.read_csv(IN_PRODUCTS)

    if "product_category_name" not in products.columns:
        raise ValueError("Missing product_category_name in products_clean.csv")

    categories = (
        products[["product_category_name"]]
        .fillna("unknown")
        .drop_duplicates()
        .sort_values("product_category_name")
        .reset_index(drop=True)
        .rename(columns={"product_category_name": "category_name"})
    )

    # Générer un ID stable (1..N) après tri
    categories["category_id"] = categories.index + 1

    categories = categories[["category_id", "category_name"]]

    if categories["category_name"].duplicated().any():
        raise ValueError("Duplicate category_name found (should not happen)")

    categories.to_csv(OUT_FILE, index=False)
    print(f"[OK] Exported {len(categories):,} rows -> {OUT_FILE}")


if __name__ == "__main__":
    main()