import json
import time
import uuid
from datetime import datetime, timezone

from kafka import KafkaProducer

BROKER = "localhost:19092"
TOPIC = "phenix.transactions.e7"


def main():
    producer = KafkaProducer(
        bootstrap_servers=[BROKER],
        value_serializer=lambda value: json.dumps(value).encode("utf-8"),
        acks="all",
        retries=3,
    )

    try:
        for i in range(5):
            transaction = {
                "event_id": str(uuid.uuid4()),
                "transaction_id": f"DEMO-E7-{uuid.uuid4().hex[:12]}",
                "event_timestamp": datetime.now(timezone.utc).isoformat(),
                "amount": round(15.50 + i * 12.25, 2),
                "currency": "EUR",
                "channel": "online" if i % 2 == 0 else "store",
                "source": "phenix-e7-simulation",
            }

            future = producer.send(TOPIC, value=transaction)
            metadata = future.get(timeout=15)

            print(
                f"ENVOYE | transaction={transaction['transaction_id']} "
                f"| montant={transaction['amount']} EUR "
                f"| partition={metadata.partition} "
                f"| offset={metadata.offset}"
            )

            time.sleep(1)

        print("Production terminee : 5 transactions fictives.")

    finally:
        producer.flush()
        producer.close()


if __name__ == "__main__":
    main()
