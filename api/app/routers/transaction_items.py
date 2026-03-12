from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from app.db import engine

router = APIRouter()


@router.get("/transactions/{transaction_id}/items")
def get_transaction_items(transaction_id: str):
    transaction_query = text("""
        SELECT 1
        FROM datamarket.transactions
        WHERE transaction_id = :transaction_id
    """)

    query = text("""
        SELECT
            ti.transaction_id,
            ti.transaction_item_id,
            ti.product_id,
            ti.quantity,
            ti.unit_price,
            p.category_id,
            p.product_weight_g,
            p.product_length_cm,
            p.product_height_cm,
            p.product_width_cm
        FROM datamarket.transaction_items ti
        JOIN datamarket.products p
          ON ti.product_id = p.product_id
        WHERE ti.transaction_id = :transaction_id
        ORDER BY ti.transaction_item_id
    """)

    with engine.connect() as connection:
        transaction_exists = connection.execute(
            transaction_query,
            {"transaction_id": transaction_id}
        ).fetchone()

        if transaction_exists is None:
            raise HTTPException(status_code=404, detail="Transaction introuvable")

        result = connection.execute(
            query,
            {"transaction_id": transaction_id}
        )
        items = [dict(row._mapping) for row in result]

    return {
        "transaction_id": transaction_id,
        "total_items": len(items),
        "data": items
    }