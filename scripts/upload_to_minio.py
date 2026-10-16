
import os
import logging
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from minio import Minio

# Configuration
PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEST_DIR = PROJECT_ROOT / "data" / "tests"
LOG_DIR = PROJECT_ROOT / "logs"
BUCKET_NAME = "phenix-bronze"

load_dotenv(PROJECT_ROOT / ".env")

# Journalisation
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "minio_ingestion.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger("phenix_ingestion")


def main():
    client = Minio(
        "localhost:9000",
        access_key=os.environ["MINIO_ROOT_USER"],
        secret_key=os.environ["MINIO_ROOT_PASSWORD"],
        secure=False,
    )

    if not client.bucket_exists(BUCKET_NAME):
        raise RuntimeError(f"Bucket introuvable : {BUCKET_NAME}")

    files = sorted(TEST_DIR.glob("*.csv"))

    if not files:
        raise RuntimeError("Aucun fichier CSV trouve dans data/tests")

    logger.info("Debut ingestion batch - %s fichier(s)", len(files))

    errors = 0

    for file_path in files:
        object_name = f"tests/{file_path.name}"

        try:
            result = client.fput_object(
                BUCKET_NAME,
                object_name,
                str(file_path),
                content_type="text/csv",
                metadata={
                    "source": "phenix-test",
                    "ingestion-date": datetime.now(timezone.utc).isoformat(),
                },
            )

            logger.info(
                "SUCCESS | fichier=%s | taille=%s octets | objet=%s | etag=%s",
                file_path.name,
                file_path.stat().st_size,
                object_name,
                result.etag,
            )

        except Exception:
            errors += 1
            logger.exception("ERROR | fichier=%s", file_path.name)

    if errors:
        raise RuntimeError(f"Ingestion terminee avec {errors} erreur(s)")

    logger.info("Ingestion batch terminee avec succes")


if __name__ == "__main__":
    main()
