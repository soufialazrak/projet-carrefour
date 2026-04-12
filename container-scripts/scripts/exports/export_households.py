import os
from pathlib import Path

import pandas as pd

EXPORTS_DIR = Path(__file__).resolve().parent
PROJECT_DIR = EXPORTS_DIR.parent.parent
DATA_DIR = Path(os.environ.get("DATA_DIR", PROJECT_DIR / "data"))

IN_TRANSACTIONS = DATA_DIR / "transactions_enriched.csv"

OUT_DIR = DATA_DIR / "outputs"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_FILE = OUT_DIR / "households.csv"


def main():
    print("Script export_households démarré...")

    tx = pd.read_csv(IN_TRANSACTIONS)

    required_cols = {"household_id", "household_created_at"}
    missing = required_cols - set(tx.columns)
    if missing:
        raise ValueError(f"Missing columns in transactions_enriched: {missing}")

    households = (
        tx[["household_id", "household_created_at"]]
        .drop_duplicates()
        .copy()
    )

    if households["household_id"].isna().any():
        raise ValueError("Null household_id found")
    if households["household_id"].duplicated().any():
        raise ValueError("Duplicate household_id found")

    households.to_csv(OUT_FILE, index=False)
    print(f"[OK] Exported {len(households):,} rows -> {OUT_FILE}")


if __name__ == "__main__":
    main()