import os
from pathlib import Path

ROUTES = {
    "customers.csv": "customers",
    "households.csv": "households",
    "loyalty_cards.csv": "loyalty_cards",
    "product_categories.csv": "product_categories",
    "products.csv": "products",
    "transactions.csv": "transactions",
    "transaction_items.csv": "transaction_items",
}

def upload_outputs_to_adls() -> None:
    try:
        from azure.identity import DefaultAzureCredential
        from azure.storage.filedatalake import DataLakeServiceClient
    except ImportError as e:
        raise ImportError(
            "Les dépendances Azure ne sont pas installées. "
            "Installe azure-identity et azure-storage-file-datalake."
        ) from e

    account_url = os.environ["ADLS_ACCOUNT_URL"]
    filesystem_name = os.environ["ADLS_FILESYSTEM"]
    export_period = os.environ["EXPORT_PERIOD"]
    local_output_dir = Path(os.environ.get("LOCAL_OUTPUT_DIR", str(Path.cwd() / "data" / "outputs")))

    if not local_output_dir.exists():
        raise FileNotFoundError(f"Le dossier de sortie local n'existe pas : {local_output_dir}")

    credential = DefaultAzureCredential()
    service_client = DataLakeServiceClient(account_url=account_url, credential=credential)
    file_system_client = service_client.get_file_system_client(filesystem_name)

    for file_path in local_output_dir.glob("*.csv"):
        file_name = file_path.name

        if file_name not in ROUTES:
            print(f"[WARN] fichier ignoré (pas de route définie) : {file_name}")
            continue

        remote_path = f"{ROUTES[file_name]}/{export_period}/{file_name}"
        file_client = file_system_client.get_file_client(remote_path)

        with open(file_path, "rb") as f:
            content = f.read()

        # Écrasement propre du fichier cible
        file_client.create_file()
        file_client.append_data(data=content, offset=0, length=len(content))
        file_client.flush_data(len(content))

        print(f"[OK] Uploaded: {remote_path}")