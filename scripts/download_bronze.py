
import os
import logging
from pathlib import Path

from dotenv import load_dotenv
from minio import Minio

# Configuration du projet PHENIX
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEST_DIR = PROJECT_ROOT / "data" / "bronze_work"
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

# Charger les identifiants MinIO
load_dotenv(PROJECT_ROOT / ".env")

# Préparer les dossiers
DEST_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Configurer les logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(
            LOG_DIR / "bronze_download.log",
            encoding="utf-8"
        ),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger("phenix_bronze_download")


def main():
    logger.info("Debut telechargement MinIO Bronze")

    client = Minio(
        "localhost:9000",
        access_key=os.environ["MINIO_ROOT_USER"],
        secret_key=os.environ["MINIO_ROOT_PASSWORD"],
        secure=False,
    )

    if not client.bucket_exists(BUCKET_NAME):
        raise RuntimeError(
            f"Bucket introuvable : {BUCKET_NAME}"
        )

    for filename in EXPECTED_FILES:
        object_name = f"{OBJECT_PREFIX}/{filename}"
        destination = DEST_DIR / filename
        temporary = DEST_DIR / f"{filename}.part"

        logger.info("Telechargement : %s", object_name)

        try:
            # Vérifier l'objet distant
            remote = client.stat_object(
                BUCKET_NAME,
                object_name
            )

            if remote.size == 0:
                raise ValueError(
                    f"Fichier distant vide : {object_name}"
                )

            # Télécharger dans un fichier temporaire
            client.fget_object(
                BUCKET_NAME,
                object_name,
                str(temporary)
            )

            # Vérifier la taille téléchargée
            local_size = temporary.stat().st_size

            if local_size != remote.size:
                raise ValueError(
                    f"Taille incorrecte pour {filename} : "
                    f"{local_size} != {remote.size}"
                )

            # Remplacer le fichier uniquement après validation
            temporary.replace(destination)

            logger.info(
                "SUCCESS | fichier=%s | taille=%s octets",
                filename,
                local_size
            )

        except Exception:
            logger.exception(
                "ERROR | fichier=%s",
                filename
            )
            raise

    logger.info(
        "Telechargement Bronze termine avec succes - %s fichiers",
        len(EXPECTED_FILES)
    )


if __name__ == "__main__":
    main()
