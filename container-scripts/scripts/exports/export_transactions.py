import os
from pathlib import Path

import pandas as pd

EXPORTS_DIR = Path(__file__).resolve().parent
PROJECT_DIR = EXPORTS_DIR.parent.parent
DATA_DIR = Path(os.environ.get("DATA_DIR", PROJECT_DIR / "data"))

IN_TRANSACTIONS = DATA_DIR / "transactions_enriched.csv"

OUT_DIR = DATA_DIR / "outputs"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_FILE = OUT_DIR / "transactions.csv"


def main():
    print("Script export_transactions démarré...")

    tx = pd.read_csv(IN_TRANSACTIONS)

    required_cols = [
        "transaction_id",
        "card_id",
        "transaction_status",
        "channel",
        "payment_types_used",
        "transaction_timestamp",
    ]

    missing = set(required_cols) - set(tx.columns)
    if missing:
        raise ValueError(f"Missing columns in transactions_enriched: {missing}")

    transactions = (
        tx[required_cols]
        .drop_duplicates(subset=["transaction_id"])
        .copy()
    )

    if transactions["transaction_id"].isna().any():
        raise ValueError("Null transaction_id found")

    if transactions["transaction_id"].duplicated().any():
        raise ValueError("Duplicate transaction_id found")

    if transactions["card_id"].isna().any():
        raise ValueError("Null card_id found in transactions")

    transactions.to_csv(OUT_FILE, index=False)
    print(f"[OK] Exported {len(transactions):,} rows -> {OUT_FILE}")


if __name__ == "__main__":
    main()