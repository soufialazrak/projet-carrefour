
import json
import os
from decimal import Decimal
from io import BytesIO
from urllib.parse import urlsplit, urlunsplit
from uuid import UUID

import psycopg2
from dotenv import load_dotenv
from minio import Minio


# Configuration
load_dotenv()

BUCKET = "phenix-silver"
PREFIX = "streaming/transactions/"


def get_database_url():
    """Adapte la connexion PostgreSQL selon l'environnement."""
    url = os.environ["DATABASE_URL"]

    # Dans Airflow, conserver l'adresse PostgreSQL du réseau Docker.
    if os.getenv("RUNNING_IN_DOCKER") == "1":
        return url

    # Sur Windows, conserver la connexion locale existante.
    parsed = urlsplit(url)

    if parsed.hostname == "postgres":
        username = parsed.username or ""
        password = parsed.password
        credentials = username

        if password is not None:
            credentials += ":" + password

        if credentials:
            credentials += "@"

        netloc = credentials + "localhost:5433"

        return urlunsplit(
            (parsed.scheme, netloc, parsed.path, parsed.query, parsed.fragment)
        )

    return url


def get_minio_client():
    """Connexion MinIO compatible Windows et Docker."""
    return Minio(
        os.getenv("MINIO_ENDPOINT", "localhost:9000"),
        access_key=os.environ["MINIO_ROOT_USER"],
        secret_key=os.environ["MINIO_ROOT_PASSWORD"],
        secure=False,
    )


def main():
    minio_client = get_minio_client()

    connection = psycopg2.connect(
        get_database_url(),
        connect_timeout=10,
    )

    inserted = 0
    duplicates = 0
    rejected = 0

    try:
        with connection:
            with connection.cursor() as cursor:
                objects = minio_client.list_objects(
                    BUCKET,
                    prefix=PREFIX,
                    recursive=True,
                )

                for obj in objects:
                    if not obj.object_name.endswith(".json"):
                        continue

                    cursor.execute("SAVEPOINT event_ingestion")
                    response = None

                    try:
                        response = minio_client.get_object(
                            BUCKET,
                            obj.object_name,
                        )

                        event = json.loads(response.read())

                        event_id = str(UUID(event["event_id"]))
                        transaction_id = str(event["transaction_id"])
                        timestamp = event["event_timestamp"]
                        amount = Decimal(str(event["amount"]))
                        currency = event["currency"]
                        channel = event["channel"]
                        source = event["source"]

                        if not transaction_id.strip() or not str(source).strip():
                            raise ValueError("Identifiant ou source vide")

                        if not amount.is_finite():
                            raise ValueError("Montant non fini")

                        cursor.execute(
                            """
                            INSERT INTO streaming.transactions_e7 (
                                event_id,
                                transaction_id,
                                event_timestamp,
                                amount,
                                currency,
                                channel,
                                source
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (event_id) DO NOTHING
                            RETURNING event_id;
                            """,
                            (
                                event_id,
                                transaction_id,
                                timestamp,
                                amount,
                                currency,
                                channel,
                                source,
                            ),
                        )

                        if cursor.fetchone():
                            inserted += 1
                            print(f"INSERE | {transaction_id} | {amount} EUR")
                        else:
                            duplicates += 1
                            print(f"DEJA PRESENT | {transaction_id}")

                    except Exception as exc:
                        cursor.execute("ROLLBACK TO SAVEPOINT event_ingestion")
                        rejected += 1
                        print(
                            f"ERREUR | {obj.object_name} | "
                            f"{type(exc).__name__}: {exc}"
                        )

                    finally:
                        if response is not None:
                            response.close()
                            response.release_conn()

        print(
            f"TERMINE | inseres={inserted} | "
            f"deja_presents={duplicates} | rejetes={rejected}"
        )

    finally:
        connection.close()


if __name__ == "__main__":
    main()
