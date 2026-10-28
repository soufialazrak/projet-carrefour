import json
import time
import uuid
from datetime import datetime, timezone
from confluent_kafka import Producer

BROKER = "127.0.0.1:19092"
TOPIC = "phenix.transactions.e7"

def main():
    producer = Producer({
        "bootstrap.servers": BROKER,
        "acks": "all",
        "client.id": "phenix-e7-producer",
    })

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

        producer.produce(
            TOPIC,
            key=transaction["event_id"],
            value=json.dumps(transaction).encode("utf-8"),
        )
        producer.poll(0)

        print(
            f"PREPARE | transaction={transaction['transaction_id']} "
            f"| montant={transaction['amount']} EUR"
        )
        time.sleep(1)

    remaining = producer.flush(15)
    if remaining:
        raise RuntimeError(f"{remaining} message(s) non confirmes")

    print("Envoi termine : 5 transactions fictives.")

if __name__ == "__main__":
    main()
