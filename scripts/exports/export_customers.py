import os
import hashlib
import pandas as pd
from cryptography.fernet import Fernet

PROJECT_DIR = r"C:\Users\soufi\Documents\projet-carrefour"
DATA_DIR = os.path.join(PROJECT_DIR, "data")

IN_TRANSACTIONS = os.path.join(DATA_DIR, "transactions_enriched.csv")

OUT_DIR = os.path.join(DATA_DIR, "outputs")
os.makedirs(OUT_DIR, exist_ok=True)

OUT_FILE = os.path.join(OUT_DIR, "customers.csv")


def get_cipher():
    """
    Récupère la clé de chiffrement depuis la variable d'environnement.
    La clé doit être une clé Fernet valide.
    """
    key = os.environ.get("DATA_ENCRYPTION_KEY")
    if not key:
        raise ValueError(
            "La variable d'environnement DATA_ENCRYPTION_KEY est absente. "
            "Définis-la avant d'exécuter le script."
        )
    return Fernet(key.encode())


def encrypt_value(value, cipher):
    """
    Chiffre une valeur texte.
    - Si la valeur est vide ou NaN, renvoie None.
    - Sinon, convertit en texte, chiffre, puis renvoie une chaîne.
    """
    if pd.isna(value):
        return None
    value_str = str(value).strip()
    if value_str == "":
        return None
    return cipher.encrypt(value_str.encode()).decode()


def hash_email(value):
    """
    Crée un hash SHA-256 d'un email normalisé.
    Sert à faire des recherches sans stocker l'email en clair.
    """
    if pd.isna(value):
        return None
    value_str = str(value).strip().lower()
    if value_str == "":
        return None
    return hashlib.sha256(value_str.encode()).hexdigest()


def main():
    print("Script export_customers démarré...")

    tx = pd.read_csv(IN_TRANSACTIONS)

    required_cols = {
        "customer_id",
        "household_id",
        "first_name",
        "last_name",
        "birth_year",
        "email",
        "customer_city",
        "postal_code",
        "region",
    }

    missing = required_cols - set(tx.columns)
    if missing:
        raise ValueError(f"Colonnes manquantes dans transactions_enriched.csv : {missing}")

    # 1. Construction de la table customers à partir des transactions
    customers = (
        tx[[
            "customer_id",
            "household_id",
            "first_name",
            "last_name",
            "birth_year",
            "email",
            "customer_city",
            "postal_code",
            "region",
        ]]
        .drop_duplicates(subset=["customer_id"])
        .copy()
    )

    # 2. Vérifications minimales avant chiffrement
    if customers["customer_id"].isna().any():
        raise ValueError("Null customer_id trouvé")
    if customers["customer_id"].duplicated().any():
        raise ValueError("Duplicate customer_id trouvé")
    if customers["household_id"].isna().any():
        raise ValueError("Null household_id trouvé dans customers")

    # 3. Initialisation du moteur de chiffrement
    cipher = get_cipher()

    # 4. Chiffrement des colonnes sensibles
    customers["first_name_encrypted"] = customers["first_name"].apply(lambda x: encrypt_value(x, cipher))
    customers["last_name_encrypted"] = customers["last_name"].apply(lambda x: encrypt_value(x, cipher))
    customers["email_encrypted"] = customers["email"].apply(lambda x: encrypt_value(x, cipher))

    # 5. Hash de l'email pour recherche / matching
    customers["email_hash"] = customers["email"].apply(hash_email)

    # 6. Suppression des colonnes en clair
    customers = customers.drop(columns=["first_name", "last_name", "email"])

    # 7. Réorganisation des colonnes finales
    customers = customers[[
        "customer_id",
        "household_id",
        "first_name_encrypted",
        "last_name_encrypted",
        "birth_year",
        "email_encrypted",
        "email_hash",
        "customer_city",
        "postal_code",
        "region",
    ]]

    # 8. Export CSV
    customers.to_csv(OUT_FILE, index=False)
    print(f"[OK] Exported {len(customers):,} rows -> {OUT_FILE}")


if __name__ == "__main__":
    main()