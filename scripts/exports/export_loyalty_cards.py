import os
import pandas as pd

PROJECT_DIR = r"C:\Users\soufi\Documents\projet-carrefour"
DATA_DIR = os.path.join(PROJECT_DIR, "data")

IN_TRANSACTIONS = os.path.join(DATA_DIR, "transactions_enriched.csv")

OUT_DIR = os.path.join(DATA_DIR, "outputs")
os.makedirs(OUT_DIR, exist_ok=True)

OUT_FILE = os.path.join(OUT_DIR, "loyalty_cards.csv")


def main():
    print("Script export_loyalty_cards démarré...")

    tx = pd.read_csv(IN_TRANSACTIONS)

    required_cols = {"card_id", "customer_id", "card_status", "issued_at"}
    missing = required_cols - set(tx.columns)
    if missing:
        raise ValueError(f"Missing columns in transactions_enriched: {missing}")

    cards = (
        tx[["card_id", "customer_id", "card_status", "issued_at"]]
        .drop_duplicates(subset=["card_id"])
        .copy()
    )

    # contrôles
    if cards["card_id"].isna().any():
        raise ValueError("Null card_id found")
    if cards["card_id"].duplicated().any():
        raise ValueError("Duplicate card_id found")
    if cards["customer_id"].isna().any():
        raise ValueError("Null customer_id found in loyalty_cards")

    # Optionnel (à activer si tu veux imposer 1 carte max par client)
    # if cards["customer_id"].duplicated().any():
    #     raise ValueError("A customer has multiple cards (violates 1:1 assumption)")

    cards.to_csv(OUT_FILE, index=False)
    print(f"[OK] Exported {len(cards):,} rows -> {OUT_FILE}")


if __name__ == "__main__":
    main()