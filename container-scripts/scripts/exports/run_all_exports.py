import os
import subprocess
import sys
from pathlib import Path

# On ne charge Key Vault que si besoin
try:
    from keyvault_utils import get_secret
except ImportError:
    get_secret = None

SCRIPTS = [
    "export_households.py",
    "export_customers.py",
    "export_loyalty_cards.py",
    "export_product_categories.py",
    "export_products.py",
    "export_transactions.py",
    "export_transaction_items.py",
]

EXPECTED_OUTPUTS = [
    "customers.csv",
    "households.csv",
    "loyalty_cards.csv",
    "product_categories.csv",
    "products.csv",
    "transactions.csv",
    "transaction_items.csv",
]

def main():
    exports_dir = Path(__file__).resolve().parent

    # 👉 Dossier projet racine = 2 niveaux au-dessus de scripts/exports
    project_dir = exports_dir.parent.parent.parent

    # 👉 Dossier data unique pour tous les scripts
    data_dir = Path(os.environ.get("DATA_DIR", str(project_dir / "data")))
    output_dir = data_dir / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)

    # On force DATA_DIR pour tous les sous-scripts
    os.environ["DATA_DIR"] = str(data_dir)

    print("=== Run all exports ===")
    print(f"[INFO] DATA_DIR = {data_dir}")
    print(f"[INFO] OUTPUT_DIR = {output_dir}")

    # Mode local par défaut
    local_mode = os.environ.get("LOCAL_MODE", "true").lower() == "true"

    if local_mode:
        print("[LOCAL MODE] Using local encryption key")
        encryption_key = "c2VjdXJlLXRlc3Qta2V5LTEyMzQ1Njc4OTAxMjM0NTY="
    else:
        if get_secret is None:
            print("[ERROR] Azure dependencies for Key Vault are not installed.")
            sys.exit(1)

        secret_name = os.environ.get("ENCRYPTION_SECRET_NAME", "pii-encryption-key")
        encryption_key = get_secret(secret_name)
        print("[OK] Encryption key loaded from Key Vault")

    # Variable attendue par export_customers.py
    os.environ["DATA_ENCRYPTION_KEY"] = encryption_key

    # Exécution des scripts
    for script in SCRIPTS:
        script_path = exports_dir / script
        print(f"\n>>> Running: {script_path.name}")

        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            env=os.environ.copy(),
        )

        if result.returncode != 0:
            print("[ERROR]")
            print(result.stdout)
            print(result.stderr)
            sys.exit(result.returncode)
        else:
            if result.stdout.strip():
                print(result.stdout.strip())

    # Vérification des fichiers attendus
    missing = []
    for expected in EXPECTED_OUTPUTS:
        if not (output_dir / expected).exists():
            missing.append(expected)

    if missing:
        print("[ERROR] Missing expected CSV files:")
        for m in missing:
            print(f" - {m}")
        sys.exit(1)

    print("\n[OK] All expected CSV files generated successfully.")

    # Upload vers ADLS uniquement en mode Azure
    if not local_mode:
        print("\nUploading files to ADLS...")
        try:
            from upload_to_adls import upload_outputs_to_adls
        except ImportError as e:
            print("[ERROR] Unable to import upload_to_adls dependencies.")
            print(str(e))
            sys.exit(1)

        upload_outputs_to_adls()
    else:
        print("\n[LOCAL MODE] Skipping ADLS upload")

    print("\nAll exports completed successfully.")

if __name__ == "__main__":
    main()