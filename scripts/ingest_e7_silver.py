import os
from pathlib import Path

from dotenv import load_dotenv
from minio import Minio

PROJECT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_DIR / ".env")

SOURCE_DIR = PROJECT_DIR / "data" / "e7_exports"
BUCKET = "phenix-silver"
PREFIX = "e7/"

FILES = [
    "households.csv",
    "customers.csv",
    "loyalty_cards.csv",
    "product_categories.csv",
    "products.csv",
    "transactions.csv",
    "transaction_items.csv",
]


def main():
    client = Minio(
        "localhost:9000",
        access_key=os.environ["MINIO_ROOT_USER"],
        secret_key=os.environ["MINIO_ROOT_PASSWORD"],
        secure=False,
    )

    if not client.bucket_exists(BUCKET):
        raise RuntimeError(f"Bucket introuvable : {BUCKET}")

    for filename in FILES:
        source = SOURCE_DIR / filename
        destination = PREFIX + filename

        if not source.is_file():
            raise FileNotFoundError(source)

        try:
            client.stat_object(BUCKET, destination)
        except Exception as exc:
            from minio.error import S3Error
            if not isinstance(exc, S3Error) or exc.code != "NoSuchKey":
                raise
        else:
            print(f"IGNORE : {destination} existe deja")
            continue

        client.fput_object(
            BUCKET,
            destination,
            str(source),
            content_type="text/csv",
            metadata={
                "pipeline": "phenix-e7",
                "layer": "silver",
                "source": "olist-adapted-for-phenix",
            },
        )
        print(f"OK : {filename} -> {BUCKET}/{destination}")

    print("Ingestion Silver terminee.")


if __name__ == "__main__":
    main()
