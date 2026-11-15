
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "catalogue" / "catalogue_minio.csv"
DESTINATION = ROOT / "catalogue" / "catalogue_metier.csv"

DESCRIPTIONS = {
    "carrefour_customers.csv": ("Clients sources", "Personnelles"),
    "carrefour_orders.csv": ("Commandes clients sources", "Transactionnelles"),
    "carrefour_order_items.csv": ("Articles des commandes", "Transactionnelles"),
    "carrefour_order_payments.csv": ("Paiements des commandes", "Transactionnelles"),
    "carrefour_products.csv": ("Référentiel produits source", "Métier"),
    "carrefour_product_categories.csv": ("Catégories produits sources", "Métier"),
    "customers.csv": ("Référentiel clients préparé", "Personnelles"),
    "households.csv": ("Référentiel foyers préparé", "Pseudonymisées"),
    "loyalty_cards.csv": ("Cartes de fidélité préparées", "Personnelles"),
    "product_categories.csv": ("Catégories produits préparées", "Métier"),
    "products.csv": ("Référentiel produits préparé", "Métier"),
    "transactions.csv": ("Transactions préparées", "Transactionnelles"),
    "transaction_items.csv": ("Lignes de transactions préparées", "Transactionnelles"),
}

def enrichir(ligne):
    chemin = ligne["chemin_objet"]
    nom = Path(chemin).name

    if chemin.startswith("tests/"):
        description = "Fichier de test technique MinIO"
        classification = "Test - sensibilité à vérifier"
        usage = "Vérification technique"
    elif chemin.startswith("streaming/"):
        description = "Événement transactionnel simulé"
        classification = "Transactionnelles"
        usage = "Pipeline Streaming E7"
    else:
        description, classification = DESCRIPTIONS.get(
            nom, ("Description à compléter", "À classifier")
        )
        usage = "Pipeline Batch E7"

    return {
        **ligne,
        "description_metier": description,
        "classification_proposee": classification,
        "usage": usage,
    }

with SOURCE.open(encoding="utf-8-sig", newline="") as f:
    lignes = list(csv.DictReader(f, delimiter=";"))

resultats = [enrichir(ligne) for ligne in lignes]

with DESTINATION.open("w", encoding="utf-8-sig", newline="") as f:
    colonnes = list(resultats[0].keys())
    writer = csv.DictWriter(f, fieldnames=colonnes, delimiter=";")
    writer.writeheader()
    writer.writerows(resultats)

print(f"Catalogue enrichi : {DESTINATION}")
print(f"Objets documentés : {len(resultats)}")
