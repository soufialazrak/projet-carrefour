from fastapi import APIRouter, Query
from sqlalchemy import text

from app.db import engine

router = APIRouter(prefix="/streaming", tags=["Streaming"])


@router.get("/transactions")
def get_streaming_transactions(
    limit: int = Query(default=50, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
):
    """Consulter les transactions Kafka stockées dans PostgreSQL."""

    query = text("""
        SELECT
            event_id,
            transaction_id,
            event_timestamp,
            amount,
            currency,
            channel,
            source,
            ingested_at
        FROM streaming.transactions_e7
        ORDER BY event_timestamp DESC, event_id DESC
        LIMIT :limit OFFSET :offset
    """)

    count_query = text("""
        SELECT COUNT(*)
        FROM streaming.transactions_e7
    """)

    with engine.connect() as connection:
        total = connection.execute(count_query).scalar_one()
        rows = connection.execute(
            query,
            {"limit": limit, "offset": offset}
        ).fetchall()

    transactions = []

    for row in rows:
        data = row._mapping

        transactions.append({
            "event_id": str(data["event_id"]),
            "transaction_id": data["transaction_id"],
            "event_timestamp": data["event_timestamp"].isoformat(),
            "amount": float(data["amount"]),
            "currency": data["currency"],
            "channel": data["channel"],
            "source": data["source"],
            "ingested_at": data["ingested_at"].isoformat(),
        })

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "transactions": transactions,
    }