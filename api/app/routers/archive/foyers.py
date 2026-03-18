from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text
from app.db import engine

router = APIRouter()


@router.get("/foyers")
def get_foyers(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    query = text("""
        SELECT *
        FROM datamarket.foyers
        ORDER BY foyer_id
        LIMIT :limit OFFSET :offset
    """)

    count_query = text("""
        SELECT COUNT(*) AS total
        FROM datamarket.foyers
    """)

    with engine.connect() as connection:
        result = connection.execute(query, {"limit": limit, "offset": offset})
        foyers = [dict(row._mapping) for row in result]

        total_result = connection.execute(count_query)
        total = total_result.scalar()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "data": foyers
    }


@router.get("/foyers/{foyer_id}")
def get_foyer_by_id(foyer_id: str):
    query = text("""
        SELECT *
        FROM datamarket.foyers
        WHERE foyer_id = :foyer_id
    """)

    with engine.connect() as connection:
        result = connection.execute(query, {"foyer_id": foyer_id})
        foyer = result.fetchone()

    if foyer is None:
        raise HTTPException(status_code=404, detail="Foyer introuvable")

    return dict(foyer._mapping)


@router.get("/foyers/{foyer_id}/clients")
def get_clients_by_foyer_id(
    foyer_id: str,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    foyer_query = text("""
        SELECT 1
        FROM datamarket.foyers
        WHERE foyer_id = :foyer_id
    """)

    query = text("""
        SELECT customer_id, foyer_id, customer_city, customer_state
        FROM datamarket.customers
        WHERE foyer_id = :foyer_id
        ORDER BY customer_id
        LIMIT :limit OFFSET :offset
    """)

    count_query = text("""
        SELECT COUNT(*) AS total
        FROM datamarket.customers
        WHERE foyer_id = :foyer_id
    """)

    with engine.connect() as connection:
        foyer_exists = connection.execute(foyer_query, {"foyer_id": foyer_id}).fetchone()

        if foyer_exists is None:
            raise HTTPException(status_code=404, detail="Foyer introuvable")

        result = connection.execute(
            query,
            {"foyer_id": foyer_id, "limit": limit, "offset": offset}
        )
        clients = [dict(row._mapping) for row in result]

        total_result = connection.execute(count_query, {"foyer_id": foyer_id})
        total = total_result.scalar()

    return {
        "foyer_id": foyer_id,
        "total": total,
        "limit": limit,
        "offset": offset,
        "data": clients
    }