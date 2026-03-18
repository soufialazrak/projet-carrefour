from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text
from app.db import engine

router = APIRouter()


@router.get("/transactions")
def get_transactions(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    query = text("""
        SELECT *
        FROM datamarket.transactions
        ORDER BY transaction_timestamp DESC
        LIMIT :limit OFFSET :offset
    """)

    count_query = text("""
        SELECT COUNT(*) FROM datamarket.transactions
    """)

    with engine.connect() as connection:
        result = connection.execute(query, {"limit": limit, "offset": offset})
        transactions = [dict(row._mapping) for row in result]

        total = connection.execute(count_query).scalar()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "data": transactions
    }


@router.get("/transactions/{transaction_id}")
def get_transaction_by_id(transaction_id: str):

    query = text("""
        SELECT *
        FROM datamarket.transactions
        WHERE transaction_id = :transaction_id
    """)

    with engine.connect() as connection:
        result = connection.execute(query, {"transaction_id": transaction_id})
        transaction = result.fetchone()

    if transaction is None:
        raise HTTPException(status_code=404, detail="Transaction introuvable")

    return dict(transaction._mapping)


@router.get("/clients/{customer_id}/transactions")
def get_transactions_by_customer_id(
    customer_id: str,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):

    query = text("""
        SELECT t.*
        FROM datamarket.transactions t
        JOIN datamarket.loyalty_cards lc
            ON t.card_id = lc.card_id
        WHERE lc.customer_id = :customer_id
        ORDER BY t.transaction_timestamp DESC
        LIMIT :limit OFFSET :offset
    """)

    count_query = text("""
        SELECT COUNT(*)
        FROM datamarket.transactions t
        JOIN datamarket.loyalty_cards lc
            ON t.card_id = lc.card_id
        WHERE lc.customer_id = :customer_id
    """)

    with engine.connect() as connection:

        result = connection.execute(
            query,
            {
                "customer_id": customer_id,
                "limit": limit,
                "offset": offset
            }
        )

        transactions = [dict(row._mapping) for row in result]

        total = connection.execute(
            count_query,
            {"customer_id": customer_id}
        ).scalar()

    return {
        "customer_id": customer_id,
        "total": total,
        "limit": limit,
        "offset": offset,
        "data": transactions
    }