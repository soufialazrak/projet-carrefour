import os
import pandas as pd

PROJECT_DIR = r"C:\Users\soufi\Documents\projet-carrefour"
DATA_DIR = os.path.join(PROJECT_DIR, "data")

IN_TRANSACTIONS = os.path.join(DATA_DIR, "transactions_enriched.csv")

OUT_DIR = os.path.join(DATA_DIR, "outputs")
os.makedirs(OUT_DIR, exist_ok=True)

OUT_FILE = os.path.join(OUT_DIR, "foyers.csv")


def main():
    print("Script export_foyers démarré...")

    tx = pd.read_csv(IN_TRANSACTIONS)

    required_cols = {"foyer_id", "foyer_created_at"}
    missing = required_cols - set(tx.columns)
    if missing:
        raise ValueError(f"Missing columns in transactions_enriched: {missing}")

    foyers = (
        tx[["foyer_id", "foyer_created_at"]]
        .drop_duplicates()
        .copy()
    )
    foyers["foyer_status"] = "active"

    if foyers["foyer_id"].isna().any():
        raise ValueError("Null foyer_id found")
    if foyers["foyer_id"].duplicated().any():
        raise ValueError("Duplicate foyer_id found")

    foyers.to_csv(OUT_FILE, index=False)
    print(f"[OK] Exported {len(foyers):,} rows -> {OUT_FILE}")


if __name__ == "__main__":
    main()