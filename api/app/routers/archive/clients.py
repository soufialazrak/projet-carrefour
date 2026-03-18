from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text
from app.db import engine

router = APIRouter()


@router.get("/clients")
def get_clients(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    query = text("""
        SELECT customer_id, foyer_id, customer_city, customer_state
        FROM datamarket.customers
        ORDER BY customer_id
        LIMIT :limit OFFSET :offset
    """)

    count_query = text("""
        SELECT COUNT(*) AS total
        FROM datamarket.customers
    """)

    with engine.connect() as connection:
        result = connection.execute(query, {"limit": limit, "offset": offset})
        clients = [dict(row._mapping) for row in result]

        total_result = connection.execute(count_query)
        total = total_result.scalar()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "data": clients
    }


@router.get("/clients/{customer_id}")
def get_client_by_id(customer_id: str):
    query = text("""
        SELECT customer_id, foyer_id, customer_city, customer_state
        FROM datamarket.customers
        WHERE customer_id = :customer_id
    """)

    with engine.connect() as connection:
        result = connection.execute(query, {"customer_id": customer_id})
        client = result.fetchone()

    if client is None:
        raise HTTPException(status_code=404, detail="Client introuvable")

    return dict(client._mapping)