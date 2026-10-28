import io
import json
import os
import uuid
from pathlib import Path
from datetime import datetime

from confluent_kafka import Consumer, KafkaException
from dotenv import load_dotenv
from minio import Minio
from minio.error import S3Error

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

TOPIC = "phenix.transactions.e7"
BUCKET = "phenix-bronze"
PREFIX = "streaming/transactions/"
MAX_MESSAGES = 6

def validate_event(event):
    required = {
        "event_id", "transaction_id", "event_timestamp",
        "amount", "currency", "channel", "source"
    }
    if not isinstance(event, dict) or not required.issubset(event):
        raise ValueError("Champs obligatoires manquants")
    uuid.UUID(str(event["event_id"]))
    datetime.fromisoformat(event["event_timestamp"].replace("Z", "+00:00"))
    if isinstance(event["amount"], bool) or not isinstance(event["amount"], (int, float)):
        raise ValueError("Montant invalide")
    if not 0 <= event["amount"] < 1000000:
        raise ValueError("Montant hors limites")
    return event

def main():
    client = Minio(
        "localhost:9000",
        access_key=os.environ["MINIO_ROOT_USER"],
        secret_key=os.environ["MINIO_ROOT_PASSWORD"],
        secure=False
    )

    if not client.bucket_exists(BUCKET):
        raise RuntimeError(f"Bucket absent : {BUCKET}")

    consumer = Consumer({
        "bootstrap.servers": "127.0.0.1:19092",
        "group.id": "phenix-e7-bronze-v1",
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False,
        "enable.partition.eof": True
    })

    consumer.subscribe([TOPIC])
    saved = 0
    duplicates = 0
    idle = 0

    try:
        while saved + duplicates < MAX_MESSAGES and idle < 10:
            msg = consumer.poll(2.0)
            if msg is None:
                idle += 1
                continue
            if msg.error():
                if msg.error().code() == -191:
                    idle += 1
                    continue
                raise KafkaException(msg.error())

            idle = 0
            event = validate_event(json.loads(msg.value().decode("utf-8")))
            key = f"{PREFIX}{event['event_id']}.json"

            try:
                response = client.stat_object(BUCKET, key)
                response = None
                duplicates += 1
                print(f"DEJA PRESENT | offset={msg.offset()} | {key}")
            except S3Error as exc:
                if exc.code not in ("NoSuchKey", "NoSuchObject"):
                    raise
                payload = json.dumps(event, ensure_ascii=False, indent=2).encode("utf-8")
                client.put_object(
                    BUCKET, key, io.BytesIO(payload), len(payload),
                    content_type="application/json"
                )
                saved += 1
                print(f"STOCKE BRONZE | offset={msg.offset()} | {key}")

            consumer.commit(message=msg, asynchronous=False)

        print(f"TERMINE | nouveaux={saved} | deja_presents={duplicates}")
    finally:
        consumer.close()

if __name__ == "__main__":
    main()
