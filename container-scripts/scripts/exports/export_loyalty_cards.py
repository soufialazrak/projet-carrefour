import os
from pathlib import Path

import pandas as pd

EXPORTS_DIR = Path(__file__).resolve().parent
PROJECT_DIR = EXPORTS_DIR.parent.parent
DATA_DIR = Path(os.environ.get("DATA_DIR", PROJECT_DIR / "data"))

IN_TRANSACTIONS = DATA_DIR / "transactions_enriched.csv"

OUT_DIR = DATA_DIR / "outputs"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_FILE = OUT_DIR / "loyalty_cards.csv"


def main():
    print("Script export_loyalty_cards démarré...")

    tx = pd.read_csv(IN_TRANSACTIONS)

    required_cols = {"card_id", "customer_id", "card_status", "issued_at", "last_used_at"}
    missing = required_cols - set(tx.columns)
    if missing:
        raise ValueError(f"Missing columns in transactions_enriched: {missing}")

    cards = (
        tx[["card_id", "customer_id", "card_status", "issued_at", "last_used_at"]]
        .drop_duplicates(subset=["card_id"])
        .copy()
    )

    if cards["card_id"].isna().any():
        raise ValueError("Null card_id found")
    if cards["card_id"].duplicated().any():
        raise ValueError("Duplicate card_id found")
    if cards["customer_id"].isna().any():
        raise ValueError("Null customer_id found in loyalty_cards")

    cards.to_csv(OUT_FILE, index=False)
    print(f"[OK] Exported {len(cards):,} rows -> {OUT_FILE}")


if __name__ == "__main__":
    main()