import subprocess
import sys
from pathlib import Path

SCRIPTS = [
    "export_households.py",
    "export_customers.py",
    "export_loyalty_cards.py",
    "export_product_categories.py",
    "export_products.py",
    "export_transactions.py",
    "export_transaction_items.py",
]

def main():
    exports_dir = Path(__file__).resolve().parent

    print("=== Run all exports ===")
    for script in SCRIPTS:
        script_path = exports_dir / script
        print(f"\n>>> Running: {script_path.name}")
        result = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True)
        if result.returncode != 0:
            print("[ERROR]")
            print(result.stdout)
            print(result.stderr)
            sys.exit(result.returncode)
        else:
            print(result.stdout.strip())

    print("\nAll exports completed successfully.")

if __name__ == "__main__":
    main()