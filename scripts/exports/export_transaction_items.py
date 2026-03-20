import os
import pandas as pd

PROJECT_DIR = r"C:\Users\soufi\Documents\projet-carrefour"
DATA_DIR = os.path.join(PROJECT_DIR, "data")

IN_ITEMS = os.path.join(DATA_DIR, "transaction_items_clean.csv")

OUT_DIR = os.path.join(DATA_DIR, "outputs")
os.makedirs(OUT_DIR, exist_ok=True)

OUT_FILE = os.path.join(OUT_DIR, "transaction_items.csv")


def main():
    print("Script export_transaction_items démarré...")

    items = pd.read_csv(IN_ITEMS)

    required_cols = [
        "transaction_id",
        "transaction_item_id",
        "product_id",
        "quantity",
        "unit_price",
    ]

    missing = set(required_cols) - set(items.columns)
    if missing:
        raise ValueError(f"Missing columns in transaction_items_clean: {missing}")

    items_clean = items[required_cols].copy()

    if items_clean.duplicated(subset=["transaction_id", "transaction_item_id"]).any():
        raise ValueError("Duplicate transaction_item_id per transaction found")

    items_clean.to_csv(OUT_FILE, index=False)
    print(f"[OK] Exported {len(items_clean):,} rows -> {OUT_FILE}")


if __name__ == "__main__":
    main()