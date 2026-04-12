import os
from pathlib import Path

import pandas as pd

EXPORTS_DIR = Path(__file__).resolve().parent
PROJECT_DIR = EXPORTS_DIR.parent.parent
DATA_DIR = Path(os.environ.get("DATA_DIR", PROJECT_DIR / "data"))

IN_ITEMS = DATA_DIR / "transaction_items_clean.csv"

OUT_DIR = DATA_DIR / "outputs"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_FILE = OUT_DIR / "transaction_items.csv"


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