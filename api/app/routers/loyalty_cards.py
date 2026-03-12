from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from app.db import engine

router = APIRouter()


@router.get("/clients/{customer_id}/card")
def get_loyalty_card_by_customer_id(customer_id: str):
    customer_query = text("""
        SELECT 1
        FROM datamarket.customers
        WHERE customer_id = :customer_id
    """)

    query = text("""
        SELECT
            card_id,
            customer_id,
            card_status,
            issued_at
        FROM datamarket.loyalty_cards
        WHERE customer_id = :customer_id
    """)

    with engine.connect() as connection:
        customer_exists = connection.execute(
            customer_query,
            {"customer_id": customer_id}
        ).fetchone()

        if customer_exists is None:
            raise HTTPException(status_code=404, detail="Client introuvable")

        result = connection.execute(
            query,
            {"customer_id": customer_id}
        )
        card = result.fetchone()

    if card is None:
        raise HTTPException(status_code=404, detail="Carte fidélité introuvable pour ce client")

    return dict(card._mapping)