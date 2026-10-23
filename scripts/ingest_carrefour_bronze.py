
import os
import logging
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from minio import Minio

# =====================================================
# CONFIGURATION - INGESTION BRONZE PHENIX
# =====================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIR = PROJECT_ROOT / "data" / "archive"
LOG_DIR = PROJECT_ROOT / "logs"

BUCKET_NAME = "phenix-bronze"
OBJECT_PREFIX = "carrefour"

EXPECTED_FILES = [
    "carrefour_customers.csv",
    "carrefour_orders.csv",
    "carrefour_order_items.csv",
    "carrefour_order_payments.csv",
    "carrefour_products.csv",
    "carrefour_product_categories.csv",
]

load_dotenv(PROJECT_ROOT / ".env")

# =====================================================
# JOURNALISATION
# =====================================================

LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(
            LOG_DIR / "carrefour_bronze_ingestion.log",
            encoding="utf-8",
        ),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger("phenix_bronze")

# =====================================================
# INGESTION DES FICHIERS CARREFOUR
# =====================================================

def main():

    logger.info("Debut ingestion Bronze - Projet PHENIX")

    # Connexion a MinIO
    client = Minio(
        "localhost:9000",
        access_key=os.environ["MINIO_ROOT_USER"],
        secret_key=os.environ["MINIO_ROOT_PASSWORD"],
        secure=False,
    )

    # Verification du bucket
    if not client.bucket_exists(BUCKET_NAME):
        raise RuntimeError(
            f"Bucket MinIO introuvable : {BUCKET_NAME}"
        )

    # Verification du dossier source
    if not SOURCE_DIR.is_dir():
        raise RuntimeError(
            f"Dossier source introuvable : {SOURCE_DIR}"
        )

    # Verification des six fichiers
    missing_files = [
        name
        for name in EXPECTED_FILES
        if not (SOURCE_DIR / name).is_file()
    ]

    if missing_files:
        raise RuntimeError(
            f"Fichiers manquants : {missing_files}"
        )

    logger.info(
        "Nombre de fichiers a ingerer : %s",
        len(EXPECTED_FILES),
    )

    errors = 0

    # Ingestion batch
    for filename in EXPECTED_FILES:

        file_path = SOURCE_DIR / filename
        object_name = f"{OBJECT_PREFIX}/{filename}"

        try:
            file_size = file_path.stat().st_size

            if file_size == 0:
                raise ValueError(
                    f"Fichier vide : {filename}"
                )

            result = client.fput_object(
                BUCKET_NAME,
                object_name,
                str(file_path),
                content_type="text/csv",
                metadata={
                    "source": "olist-adapted-for-phenix",
                    "dataset": "carrefour-phenix",
                    "layer": "bronze",
                    "ingestion-date": datetime.now(
                        timezone.utc
                    ).isoformat(),
                },
            )

            logger.info(
                "SUCCESS | fichier=%s | taille=%s octets | objet=%s | etag=%s",
                filename,
                file_size,
                object_name,
                result.etag,
            )

        except Exception:
            errors += 1
            logger.exception(
                "ERROR | fichier=%s",
                filename,
            )

    # Bilan de l'ingestion
    if errors:
        raise RuntimeError(
            f"Ingestion terminee avec {errors} erreur(s)"
        )

    logger.info(
        "Ingestion Bronze terminee avec succes - %s fichiers",
        len(EXPECTED_FILES),
    )


if __name__ == "__main__":
    main()
