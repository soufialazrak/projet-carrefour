import io
import json
import os
import uuid
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

from dotenv import load_dotenv
from minio import Minio

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

BRONZE_BUCKET = "phenix-bronze"
SILVER_BUCKET = "phenix-silver"
PREFIX = "streaming/transactions/"

REQUIRED_FIELDS = {
    "event_id", "transaction_id", "event_timestamp",
    "amount", "currency", "channel", "source"
}

def normalize(event):
    if not isinstance(event, dict):
        raise ValueError("Evenement JSON invalide")

    missing = REQUIRED_FIELDS - set(event)
    if missing:
        raise ValueError(f"Champs manquants : {sorted(missing)}")

    event_id = str(uuid.UUID(str(event["event_id"])))
    transaction_id = str(event["transaction_id"]).strip()
    source = str(event["source"]).strip()
    currency = str(event["currency"]).strip().upper()
    channel = str(event["channel"]).strip().lower()

    if not transaction_id or not source:
        raise ValueError("Transaction ou source vide")
    if currency != "EUR":
        raise ValueError("Devise non prise en charge")
    if channel not in {"online", "store"}:
        raise ValueError("Canal non reconnu")

    raw_amount = event["amount"]
    if isinstance(raw_amount, bool):
        raise ValueError("Montant booleen interdit")

    try:
        amount = Decimal(str(raw_amount))
    except (InvalidOperation, ValueError):
        raise ValueError("Montant non numerique")

    if not amount.is_finite() or amount < 0 or amount >= 1000000:
        raise ValueError("Montant hors limites")
    if amount.as_tuple().exponent < -2:
        raise ValueError("Plus de deux decimales")

    try:
        timestamp = datetime.fromisoformat(
            str(event["event_timestamp"]).replace("Z", "+00:00")
        )
    except (ValueError, TypeError):
        raise ValueError("Date invalide")

    if timestamp.tzinfo is None:
        raise ValueError("Fuseau horaire manquant")

    return {
        "event_id": event_id,
        "transaction_id": transaction_id,
        "event_timestamp": timestamp.astimezone(timezone.utc).isoformat(),
        "amount": str(amount.quantize(Decimal("0.01"))),
        "currency": currency,
        "channel": channel,
        "source": source
    }

def main():
    client = Minio(
        os.getenv("MINIO_ENDPOINT", "localhost:9000"),
        access_key=os.environ["MINIO_ROOT_USER"],
        secret_key=os.environ["MINIO_ROOT_PASSWORD"],
        secure=False
    )

    for bucket in (BRONZE_BUCKET, SILVER_BUCKET):
        if not client.bucket_exists(bucket):
            raise RuntimeError(f"Bucket absent : {bucket}")

    valid = 0
    invalid = 0

    for obj in client.list_objects(
        BRONZE_BUCKET, prefix=PREFIX, recursive=True
    ):
        if not obj.object_name.endswith(".json"):
            continue

        response = client.get_object(BRONZE_BUCKET, obj.object_name)
        try:
            raw = response.read()
        finally:
            response.close()
            response.release_conn()

        try:
            event = normalize(json.loads(raw))
        except (ValueError, TypeError, KeyError, OverflowError) as exc:
            invalid += 1
            print(f"REJETE | {obj.object_name} | {exc}")
            continue

        destination = f"{PREFIX}{event['event_id']}.json"
        payload = json.dumps(
            event, ensure_ascii=False, indent=2
        ).encode("utf-8")

        client.put_object(
            SILVER_BUCKET,
            destination,
            io.BytesIO(payload),
            len(payload),
            content_type="application/json"
        )

        valid += 1
        print(
            f"SILVER OK | {event['transaction_id']} "
            f"| {event['amount']} EUR"
        )

    print(f"TERMINE | valides={valid} | rejetes={invalid}")

if __name__ == "__main__":
    main()
