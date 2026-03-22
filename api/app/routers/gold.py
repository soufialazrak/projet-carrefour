import os
from typing import Optional

from cryptography.fernet import Fernet
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text

from app.db import engine

router = APIRouter()


# =========================
# HELPERS
# =========================

def get_cipher() -> Fernet:
    key = os.getenv("DATA_ENCRYPTION_KEY")
    if not key:
        raise RuntimeError("DATA_ENCRYPTION_KEY is missing")
    return Fernet(key.encode())


def decrypt_value(value: Optional[str]) -> Optional[str]:
    if value is None or value == "":
        return None
    cipher = get_cipher()
    return cipher.decrypt(value.encode()).decode()


def to_iso(value):
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


# =========================
# PAGE ACCUEIL
# =========================

@router.get("/gold/kpis")
def get_kpis():
    query = text("""
        SELECT
            (SELECT COUNT(*) FROM datamarket.customers) AS nombre_clients,
            (SELECT COUNT(*) FROM datamarket.households) AS nombre_households,
            (SELECT COUNT(*) FROM datamarket.transactions) AS nombre_transactions,
            (
                SELECT COALESCE(SUM(transaction_amount), 0)
                FROM gold.transaction_amount
            ) AS chiffre_affaires_total
    """)

    with engine.connect() as connection:
        row = connection.execute(query).fetchone()

    if row is None:
        return {
            "nombre_clients": 0,
            "nombre_households": 0,
            "nombre_transactions": 0,
            "chiffre_affaires_total": 0.0
        }

    data = dict(row._mapping)

    return {
        "nombre_clients": int(data["nombre_clients"]),
        "nombre_households": int(data["nombre_households"]),
        "nombre_transactions": int(data["nombre_transactions"]),
        "chiffre_affaires_total": float(data["chiffre_affaires_total"]),
    }


@router.get("/gold/revenue_over_time")
def revenue_over_time():
    query = text("""
        SELECT
            DATE_TRUNC('month', transaction_timestamp)::date AS month,
            SUM(transaction_amount) AS revenue
        FROM gold.transaction_amount
        GROUP BY DATE_TRUNC('month', transaction_timestamp)
        ORDER BY month
    """)

    with engine.connect() as connection:
        rows = connection.execute(query).fetchall()

    return [
        {
            "month": to_iso(row._mapping["month"]),
            "revenue": float(row._mapping["revenue"]),
        }
        for row in rows
    ]


# =========================
# PAGE SEGMENTATION RFM HOUSEHOLD
# =========================

@router.get("/gold/rfm/distributions")
def get_rfm_distributions():
    macro_query = text("""
        SELECT
            macro_segment,
            COUNT(*) AS count
        FROM gold.household_rfm_segments
        GROUP BY macro_segment
        ORDER BY count DESC
    """)

    recency_query = text("""
        SELECT
            recency_segment,
            COUNT(*) AS count
        FROM gold.household_rfm_segments
        GROUP BY recency_segment
        ORDER BY count DESC
    """)

    frequency_query = text("""
        SELECT
            frequency_segment,
            COUNT(*) AS count
        FROM gold.household_rfm_segments
        GROUP BY frequency_segment
        ORDER BY count DESC
    """)

    monetary_query = text("""
        SELECT
            monetary_segment,
            COUNT(*) AS count
        FROM gold.household_rfm_segments
        GROUP BY monetary_segment
        ORDER BY count DESC
    """)

    with engine.connect() as connection:
        macro_rows = connection.execute(macro_query).fetchall()
        recency_rows = connection.execute(recency_query).fetchall()
        frequency_rows = connection.execute(frequency_query).fetchall()
        monetary_rows = connection.execute(monetary_query).fetchall()

    macro_segments = [
        {
            "macro_segment": row._mapping["macro_segment"],
            "count": int(row._mapping["count"]),
        }
        for row in macro_rows
    ]

    recency_segments = [
        {
            "recency_segment": row._mapping["recency_segment"],
            "count": int(row._mapping["count"]),
        }
        for row in recency_rows
    ]

    frequency_segments = [
        {
            "frequency_segment": row._mapping["frequency_segment"],
            "count": int(row._mapping["count"]),
        }
        for row in frequency_rows
    ]

    monetary_segments = [
        {
            "monetary_segment": row._mapping["monetary_segment"],
            "count": int(row._mapping["count"]),
        }
        for row in monetary_rows
    ]

    total_households = sum(item["count"] for item in macro_segments)

    return {
        "total_households": total_households,
        "macro_segments": macro_segments,
        "recency_segments": recency_segments,
        "frequency_segments": frequency_segments,
        "monetary_segments": monetary_segments,
    }


# =========================
# PAGE SEGMENTATION CLIENT
# =========================

@router.get("/gold/customer-segmentation/distributions")
def get_customer_segmentation_distributions():
    query = text("""
        SELECT
            customer_segment,
            COUNT(*) AS count
        FROM gold.customer_segmentation
        GROUP BY customer_segment
        ORDER BY count DESC
    """)

    with engine.connect() as connection:
        rows = connection.execute(query).fetchall()

    segments = [
        {
            "customer_segment": row._mapping["customer_segment"],
            "count": int(row._mapping["count"]),
        }
        for row in rows
    ]

    total_clients = sum(item["count"] for item in segments)

    return {
        "total_clients": total_clients,
        "segments": segments,
    }


@router.get("/gold/customer-segmentation/by-region")
def get_customer_segmentation_by_region():
    query = text("""
        SELECT
            c.region,
            cs.customer_segment,
            COUNT(*) AS count
        FROM gold.customer_segmentation cs
        JOIN datamarket.customers c
            ON cs.customer_id = c.customer_id
        GROUP BY c.region, cs.customer_segment
        ORDER BY c.region, count DESC
    """)

    with engine.connect() as connection:
        rows = connection.execute(query).fetchall()

    return [
        {
            "region": row._mapping["region"],
            "customer_segment": row._mapping["customer_segment"],
            "count": int(row._mapping["count"]),
        }
        for row in rows
    ]


@router.get("/gold/customer-segmentation/list")
def list_customer_segmentation(limit: int = 50):
    query = text("""
        SELECT
            cs.customer_id,
            cs.customer_segment,
            cv.nb_transactions,
            cv.total_spent,
            cv.avg_item_price,
            c.region,
            c.customer_city
        FROM gold.customer_segmentation cs
        JOIN gold.customer_value cv
            ON cs.customer_id = cv.customer_id
        JOIN datamarket.customers c
            ON cs.customer_id = c.customer_id
        ORDER BY cv.total_spent DESC NULLS LAST, cs.customer_id
        LIMIT :limit
    """)

    with engine.connect() as connection:
        rows = connection.execute(query, {"limit": limit}).fetchall()

    return [
        {
            "customer_id": row._mapping["customer_id"],
            "customer_segment": row._mapping["customer_segment"],
            "nb_transactions": int(row._mapping["nb_transactions"] or 0),
            "total_spent": float(row._mapping["total_spent"] or 0),
            "avg_item_price": float(row._mapping["avg_item_price"] or 0),
            "region": row._mapping["region"],
            "customer_city": row._mapping["customer_city"],
        }
        for row in rows
    ]


@router.get("/gold/customer-segmentation/search")
def search_customer_segmentation(
    customer_id: Optional[str] = Query(default=None),
    email_hash: Optional[str] = Query(default=None),
):
    if not customer_id and not email_hash:
        raise HTTPException(
            status_code=400,
            detail="Provide either customer_id or email_hash",
        )

    if customer_id and email_hash:
        raise HTTPException(
            status_code=400,
            detail="Provide only one search parameter: customer_id or email_hash",
        )

    base_query = """
        SELECT
            c.customer_id,
            c.household_id,
            c.first_name_encrypted,
            c.last_name_encrypted,
            c.birth_year,
            c.email_encrypted,
            c.email_hash,
            c.customer_city,
            c.postal_code,
            c.region,
            cv.nb_transactions,
            cv.total_spent,
            cv.avg_item_price,
            cs.customer_segment
        FROM datamarket.customers c
        LEFT JOIN gold.customer_value cv
            ON c.customer_id = cv.customer_id
        LEFT JOIN gold.customer_segmentation cs
            ON c.customer_id = cs.customer_id
    """

    params = {}
    if customer_id:
        base_query += " WHERE c.customer_id = :customer_id"
        params["customer_id"] = customer_id
    else:
        base_query += " WHERE c.email_hash = :email_hash"
        params["email_hash"] = email_hash

    customer_query = text(base_query)

    try:
        with engine.connect() as connection:
            customer_row = connection.execute(customer_query, params).fetchone()

            if customer_row is None:
                raise HTTPException(status_code=404, detail="Client introuvable")

            customer_data = dict(customer_row._mapping)
            current_customer_id = customer_data["customer_id"]
            household_id = customer_data["household_id"]

            household_query = text("""
                SELECT
                    household_id,
                    household_created_at
                FROM datamarket.households
                WHERE household_id = :household_id
            """)

            household_row = connection.execute(
                household_query, {"household_id": household_id}
            ).fetchone()

            household = (
                {
                    "household_id": household_row._mapping["household_id"],
                    "household_created_at": to_iso(
                        household_row._mapping["household_created_at"]
                    ),
                }
                if household_row
                else None
            )

            household_segmentation_query = text("""
                SELECT
                    household_id,
                    last_purchase_date,
                    recency_days,
                    frequency,
                    monetary,
                    recency_segment,
                    frequency_segment,
                    monetary_segment,
                    macro_segment
                FROM gold.household_rfm_segments
                WHERE household_id = :household_id
            """)

            household_segmentation_row = connection.execute(
                household_segmentation_query, {"household_id": household_id}
            ).fetchone()

            household_segmentation = (
                {
                    "household_id": household_segmentation_row._mapping["household_id"],
                    "last_purchase_date": to_iso(
                        household_segmentation_row._mapping["last_purchase_date"]
                    ),
                    "recency_days": int(
                        household_segmentation_row._mapping["recency_days"]
                    ),
                    "frequency": int(
                        household_segmentation_row._mapping["frequency"]
                    ),
                    "monetary": float(
                        household_segmentation_row._mapping["monetary"]
                    ),
                    "recency_segment": household_segmentation_row._mapping["recency_segment"],
                    "frequency_segment": household_segmentation_row._mapping["frequency_segment"],
                    "monetary_segment": household_segmentation_row._mapping["monetary_segment"],
                    "macro_segment": household_segmentation_row._mapping["macro_segment"],
                }
                if household_segmentation_row
                else None
            )

            cards_query = text("""
                SELECT
                    card_id,
                    card_status,
                    issued_at,
                    last_used_at
                FROM datamarket.loyalty_cards
                WHERE customer_id = :customer_id
                ORDER BY issued_at
            """)

            cards_rows = connection.execute(
                cards_query, {"customer_id": current_customer_id}
            ).fetchall()

            loyalty_cards = [
                {
                    "card_id": row._mapping["card_id"],
                    "card_status": row._mapping["card_status"],
                    "issued_at": to_iso(row._mapping["issued_at"]),
                    "last_used_at": to_iso(row._mapping["last_used_at"]),
                }
                for row in cards_rows
            ]

            transactions_query = text("""
                SELECT
                    transaction_id,
                    transaction_timestamp,
                    transaction_amount
                FROM gold.transaction_amount
                WHERE customer_id = :customer_id
                ORDER BY transaction_timestamp DESC
            """)

            transactions_rows = connection.execute(
                transactions_query, {"customer_id": current_customer_id}
            ).fetchall()

            transactions = [
                {
                    "transaction_id": row._mapping["transaction_id"],
                    "transaction_timestamp": to_iso(
                        row._mapping["transaction_timestamp"]
                    ),
                    "transaction_amount": float(row._mapping["transaction_amount"] or 0),
                }
                for row in transactions_rows
            ]

    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    customer = {
        "customer_id": customer_data["customer_id"],
        "household_id": customer_data["household_id"],
        "first_name": decrypt_value(customer_data["first_name_encrypted"]),
        "last_name": decrypt_value(customer_data["last_name_encrypted"]),
        "birth_year": customer_data["birth_year"],
        "email": decrypt_value(customer_data["email_encrypted"]),
        "email_hash": customer_data["email_hash"],
        "customer_city": customer_data["customer_city"],
        "postal_code": customer_data["postal_code"],
        "region": customer_data["region"],
        "nb_transactions": int(customer_data["nb_transactions"] or 0),
        "total_spent": float(customer_data["total_spent"] or 0),
        "avg_item_price": float(customer_data["avg_item_price"] or 0),
        "customer_segment": customer_data["customer_segment"],
    }

    return {
        "customer": customer,
        "household": household,
        "household_segmentation": household_segmentation,
        "loyalty_cards": loyalty_cards,
        "transactions": transactions,
    }


# =========================
# PAGE RECHERCHE HOUSEHOLDS
# =========================

@router.get("/search/households")
def list_households(limit: int = 50):
    query = text("""
        SELECT
            h.household_id,
            h.household_created_at
        FROM datamarket.households h
        ORDER BY h.household_id
        LIMIT :limit
    """)

    with engine.connect() as connection:
        rows = connection.execute(query, {"limit": limit}).fetchall()

    return [
        {
            "household_id": row._mapping["household_id"],
            "household_created_at": to_iso(row._mapping["household_created_at"]),
        }
        for row in rows
    ]


@router.get("/search/household/{household_id}")
def search_household(household_id: str):
    household_query = text("""
        SELECT
            household_id,
            household_created_at
        FROM datamarket.households
        WHERE household_id = :household_id
    """)

    try:
        with engine.connect() as connection:
            household_row = connection.execute(
                household_query, {"household_id": household_id}
            ).fetchone()

            if household_row is None:
                raise HTTPException(status_code=404, detail="Household introuvable")

            household = {
                "household_id": household_row._mapping["household_id"],
                "household_created_at": to_iso(
                    household_row._mapping["household_created_at"]
                ),
            }

            segmentation_query = text("""
                SELECT
                    household_id,
                    last_purchase_date,
                    recency_days,
                    frequency,
                    monetary,
                    recency_segment,
                    frequency_segment,
                    monetary_segment,
                    macro_segment
                FROM gold.household_rfm_segments
                WHERE household_id = :household_id
            """)

            segmentation_row = connection.execute(
                segmentation_query, {"household_id": household_id}
            ).fetchone()

            household_segmentation = (
                {
                    "household_id": segmentation_row._mapping["household_id"],
                    "last_purchase_date": to_iso(
                        segmentation_row._mapping["last_purchase_date"]
                    ),
                    "recency_days": int(segmentation_row._mapping["recency_days"]),
                    "frequency": int(segmentation_row._mapping["frequency"]),
                    "monetary": float(segmentation_row._mapping["monetary"]),
                    "recency_segment": segmentation_row._mapping["recency_segment"],
                    "frequency_segment": segmentation_row._mapping["frequency_segment"],
                    "monetary_segment": segmentation_row._mapping["monetary_segment"],
                    "macro_segment": segmentation_row._mapping["macro_segment"],
                }
                if segmentation_row
                else None
            )

            customers_query = text("""
                SELECT
                    customer_id,
                    first_name_encrypted,
                    last_name_encrypted,
                    email_encrypted,
                    email_hash,
                    birth_year,
                    customer_city,
                    postal_code,
                    region
                FROM datamarket.customers
                WHERE household_id = :household_id
                ORDER BY customer_id
            """)

            customer_rows = connection.execute(
                customers_query, {"household_id": household_id}
            ).fetchall()

            customers = []
            for row in customer_rows:
                data = dict(row._mapping)
                customers.append(
                    {
                        "customer_id": data["customer_id"],
                        "first_name": decrypt_value(data["first_name_encrypted"]),
                        "last_name": decrypt_value(data["last_name_encrypted"]),
                        "email": decrypt_value(data["email_encrypted"]),
                        "email_hash": data["email_hash"],
                        "birth_year": data["birth_year"],
                        "customer_city": data["customer_city"],
                        "postal_code": data["postal_code"],
                        "region": data["region"],
                    }
                )

            transactions_query = text("""
                SELECT
                    transaction_id,
                    customer_id,
                    transaction_timestamp,
                    transaction_amount
                FROM gold.transaction_amount
                WHERE household_id = :household_id
                ORDER BY transaction_timestamp DESC
            """)

            transaction_rows = connection.execute(
                transactions_query, {"household_id": household_id}
            ).fetchall()

            transactions = [
                {
                    "transaction_id": row._mapping["transaction_id"],
                    "customer_id": row._mapping["customer_id"],
                    "transaction_timestamp": to_iso(
                        row._mapping["transaction_timestamp"]
                    ),
                    "transaction_amount": float(row._mapping["transaction_amount"] or 0),
                }
                for row in transaction_rows
            ]

    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "household": household,
        "household_segmentation": household_segmentation,
        "customers": customers,
        "transactions": transactions,
    }