
import os
import io
from pathlib import Path

import psycopg2
from dotenv import load_dotenv
from minio import Minio

PROJECT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_DIR / ".env")

BUCKET = "phenix-silver"
PREFIX = "e7/"

# Ordre respectant les dépendances entre tables
TABLES = [
    ("product_categories", "category_id, category_name"),
    ("products", "product_id, category_id, product_weight_g, product_length_cm, product_height_cm, product_width_cm"),
    ("households", "household_id, household_created_at"),
    ("customers", "customer_id, household_id, first_name_encrypted, last_name_encrypted, birth_year, email_encrypted, email_hash, customer_city, postal_code, region"),
    ("loyalty_cards", "card_id, customer_id, card_status, issued_at, last_used_at"),
    ("transactions", "transaction_id, card_id, transaction_status, channel, payment_types_used, transaction_timestamp"),
    ("transaction_items", "transaction_id, transaction_item_id, product_id, quantity, unit_price"),
]


def main():
    minio_client = Minio(
        "localhost:9000",
        access_key=os.environ["MINIO_ROOT_USER"],
        secret_key=os.environ["MINIO_ROOT_PASSWORD"],
        secure=False,
    )

    connection = psycopg2.connect(
        host="localhost",
        port=5433,
        dbname="datamarket_carrefour",
        user="soufia",
        password=os.environ["PGPASSWORD"],
    )

    try:
        with connection:
            with connection.cursor() as cursor:
                print("Nettoyage des anciennes données...")
                cursor.execute(
                    "TRUNCATE TABLE "
                    "datamarket.transaction_items, "
                    "datamarket.transactions, "
                    "datamarket.loyalty_cards, "
                    "datamarket.customers, "
                    "datamarket.households, "
                    "datamarket.products, "
                    "datamarket.product_categories CASCADE"
                )

                for table, columns in TABLES:
                    object_name = f"{PREFIX}{table}.csv"
                    print(f"Chargement : {object_name}")

                    response = minio_client.get_object(
                        BUCKET, object_name
                    )
                    try:
                        data = response.read()
                    finally:
                        response.close()
                        response.release_conn()

                    csv_file = io.StringIO(
                        data.decode("utf-8-sig")
                    )

                    sql = (
                        f"COPY datamarket.{table} ({columns}) "
                        "FROM STDIN WITH (FORMAT CSV, HEADER TRUE)"
                    )

                    cursor.copy_expert(sql, csv_file)

                    print(f"OK : {table}")

        print("\nChargement MinIO Silver -> PostgreSQL terminé.")

    except Exception as error:
        connection.rollback()
        print(f"\nERREUR : {error}")
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    main()
