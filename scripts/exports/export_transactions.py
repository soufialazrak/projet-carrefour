import os
import pandas as pd

PROJECT_DIR = r"C:\Users\soufi\Documents\projet-carrefour"
DATA_DIR = os.path.join(PROJECT_DIR, "data")

IN_TRANSACTIONS = os.path.join(DATA_DIR, "transactions_enriched.csv")

OUT_DIR = os.path.join(DATA_DIR, "outputs")
os.makedirs(OUT_DIR, exist_ok=True)

OUT_FILE = os.path.join(OUT_DIR, "transactions.csv")


def main():

    print("Script export_transactions démarré...")

    tx = pd.read_csv(IN_TRANSACTIONS)

    required_cols = {
        "transaction_id",
        "card_id",
        "transaction_status",
        "channel",
        "payment_types_used",
        "transaction_timestamp"
    }

    missing = required_cols - set(tx.columns)
    if missing:
        raise ValueError(f"Missing columns in transactions_enriched: {missing}")

    transactions = (
        tx[list(required_cols)]
        .drop_duplicates(subset=["transaction_id"])
        .copy()
    )

    # contrôles qualité
    if transactions["transaction_id"].isna().any():
        raise ValueError("Null transaction_id found")

    if transactions["transaction_id"].duplicated().any():
        raise ValueError("Duplicate transaction_id found")

    transactions.to_csv(OUT_FILE, index=False)

    print(f"[OK] Exported {len(transactions):,} rows -> {OUT_FILE}")


if __name__ == "__main__":
    main()