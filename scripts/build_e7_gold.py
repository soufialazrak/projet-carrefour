from pathlib import Path
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent.parent
SILVER_DIR = PROJECT_DIR / "data" / "e7_exports"
GOLD_DIR = PROJECT_DIR / "data" / "e7_gold"

OUTPUT = GOLD_DIR / "transaction_amount.csv"


def main():
    transactions = pd.read_csv(
        SILVER_DIR / "transactions.csv",
        dtype=str,
    )

    cards = pd.read_csv(
        SILVER_DIR / "loyalty_cards.csv",
        dtype=str,
    )

    customers = pd.read_csv(
        SILVER_DIR / "customers.csv",
        dtype=str,
    )

    items = pd.read_csv(
        SILVER_DIR / "transaction_items.csv",
        dtype=str,
    )

    items["quantity"] = pd.to_numeric(items["quantity"], errors="raise")
    items["unit_price"] = pd.to_numeric(items["unit_price"], errors="raise")
    items["line_amount"] = items["quantity"] * items["unit_price"]

    result = (
        transactions[["transaction_id", "card_id", "transaction_timestamp"]]
        .merge(cards[["card_id", "customer_id"]], on="card_id", how="inner", validate="many_to_one")
        .merge(customers[["customer_id", "household_id"]], on="customer_id", how="inner", validate="many_to_one")
        .merge(items[["transaction_id", "line_amount"]], on="transaction_id", how="inner", validate="one_to_many")
    )

    gold = (
        result.groupby(
            ["transaction_id", "customer_id", "household_id", "transaction_timestamp"],
            as_index=False,
        )["line_amount"]
        .sum()
        .rename(columns={"line_amount": "transaction_amount"})
    )

    GOLD_DIR.mkdir(parents=True, exist_ok=True)
    gold.to_csv(OUTPUT, index=False)

    print("OK : fichier Gold genere :", OUTPUT)
    print("Nombre de transactions :", len(gold))
    print("Montant total :", round(gold["transaction_amount"].sum(), 2))


if __name__ == "__main__":
    main()
