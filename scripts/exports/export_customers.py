import os
import pandas as pd

PROJECT_DIR = r"C:\Users\soufi\Documents\projet-carrefour"
DATA_DIR = os.path.join(PROJECT_DIR, "data")

IN_TRANSACTIONS = os.path.join(DATA_DIR, "transactions_enriched.csv")

OUT_DIR = os.path.join(DATA_DIR, "outputs")
os.makedirs(OUT_DIR, exist_ok=True)

OUT_FILE = os.path.join(OUT_DIR, "customers.csv")


def main():
    print("Script export_customers démarré...")

    tx = pd.read_csv(IN_TRANSACTIONS)

    required_cols = {"customer_id", "foyer_id", "customer_city", "customer_state"}
    missing = required_cols - set(tx.columns)
    if missing:
        raise ValueError(f"Missing columns in transactions_enriched: {missing}")

    customers = (
        tx[["customer_id", "foyer_id", "customer_city", "customer_state"]]
        .drop_duplicates(subset=["customer_id"])
        .copy()
    )

    # contrôles
    if customers["customer_id"].isna().any():
        raise ValueError("Null customer_id found")
    if customers["customer_id"].duplicated().any():
        raise ValueError("Duplicate customer_id found")
    if customers["foyer_id"].isna().any():
        raise ValueError("Null foyer_id found in customers")
    
    customers.to_csv(OUT_FILE, index=False)
    print(f"[OK] Exported {len(customers):,} rows -> {OUT_FILE}")


if __name__ == "__main__":
    main()