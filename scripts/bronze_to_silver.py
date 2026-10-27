
import os
import io
import logging
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from minio import Minio

# Configuration PHENIX
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

BRONZE_BUCKET = "phenix-bronze"
SILVER_BUCKET = "phenix-silver"

FILES = {
    "categories_test.csv": ["category_id", "category_name"],
    "products_test.csv": ["product_id", "product_name", "category_id"],
}

# Journalisation
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "bronze_to_silver.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger("phenix_silver")


def main():
    client = Minio(
        "localhost:9000",
        access_key=os.environ["MINIO_ROOT_USER"],
        secret_key=os.environ["MINIO_ROOT_PASSWORD"],
        secure=False,
    )

    if not client.bucket_exists(BRONZE_BUCKET):
        raise RuntimeError("Bucket Bronze introuvable")

    if not client.bucket_exists(SILVER_BUCKET):
        raise RuntimeError("Bucket Silver introuvable")

    for filename, required_columns in FILES.items():
        source_object = f"tests/{filename}"

        # Lecture du fichier depuis MinIO Bronze
        response = client.get_object(BRONZE_BUCKET, source_object)

        try:
            data = response.read()
        finally:
            response.close()
            response.release_conn()

        df = pd.read_csv(io.BytesIO(data), encoding="utf-8-sig")

        # Controle du schema
        missing_columns = set(required_columns) - set(df.columns)
        if missing_columns:
            raise ValueError(
                f"{filename} : colonnes manquantes {sorted(missing_columns)}"
            )

        # Conservation des colonnes attendues
        df = df[required_columns]

        # Nettoyage des valeurs
        df = df.dropna(subset=required_columns)
        df = df.drop_duplicates()

        # Validation des identifiants
        id_columns = [col for col in required_columns if col.endswith("_id")]
        for column in id_columns:
            df[column] = pd.to_numeric(df[column], errors="raise").astype("int64")

        # Preparation du fichier Silver
        output = df.to_csv(index=False).encode("utf-8")
        destination_object = f"tests/{filename}"

        # Ecriture dans MinIO Silver
        client.put_object(
            SILVER_BUCKET,
            destination_object,
            io.BytesIO(output),
            length=len(output),
            content_type="text/csv",
            metadata={
                "source-bucket": BRONZE_BUCKET,
                "transformation": "validation-deduplication",
                "transformation-date": datetime.now(timezone.utc).isoformat(),
            },
        )

        logger.info(
            "SUCCESS | fichier=%s | lignes_silver=%s | destination=%s",
            filename,
            len(df),
            destination_object,
        )

    logger.info("Transformation Bronze vers Silver terminee avec succes")


if __name__ == "__main__":
    main()
