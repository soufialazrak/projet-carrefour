from fastapi import APIRouter, Query
from sqlalchemy import text
from app.db import engine

router = APIRouter()


@router.get("/analytics/top-customers")
def get_top_customers(limit: int = Query(default=10, ge=1, le=100)):
    query = text("""
        SELECT
            c.customer_id,
            c.foyer_id,
            c.customer_city,
            c.customer_state,
            COUNT(t.transaction_id) AS nb_transactions
        FROM datamarket.customers c
        JOIN datamarket.loyalty_cards lc
          ON c.customer_id = lc.customer_id
        JOIN datamarket.transactions t
          ON lc.card_id = t.card_id
        GROUP BY
            c.customer_id,
            c.foyer_id,
            c.customer_city,
            c.customer_state
        ORDER BY nb_transactions DESC, c.customer_id
        LIMIT :limit
    """)

    with engine.connect() as connection:
        result = connection.execute(query, {"limit": limit})
        top_customers = [dict(row._mapping) for row in result]

    return {
        "limit": limit,
        "data": top_customers
    }