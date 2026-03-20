from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from app.db import engine

router = APIRouter()


# =========================
# PAGE ACCUEIL
# =========================

@router.get("/gold/kpis")
def get_kpis():
    query = text("""
        SELECT
            (SELECT COUNT(*) FROM datamarket.customers) AS nombre_clients,
            (SELECT COUNT(*) FROM datamarket.foyers) AS nombre_foyers,
            (SELECT COUNT(*) FROM datamarket.transactions) AS nombre_transactions,
            (
                SELECT COALESCE(SUM(transaction_amount), 0)
                FROM gold.transaction_amount
            ) AS chiffre_affaires_total
    """)

    with engine.connect() as connection:
        result = connection.execute(query)
        row = result.fetchone()

    if row is None:
        return {
            "nombre_clients": 0,
            "nombre_foyers": 0,
            "nombre_transactions": 0,
            "chiffre_affaires_total": 0.0
        }

    data = dict(row._mapping)

    return {
        "nombre_clients": int(data["nombre_clients"]),
        "nombre_foyers": int(data["nombre_foyers"]),
        "nombre_transactions": int(data["nombre_transactions"]),
        "chiffre_affaires_total": float(data["chiffre_affaires_total"])
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
        result = connection.execute(query)
        rows = result.fetchall()

    return [
        {
            "month": str(row._mapping["month"]),
            "revenue": float(row._mapping["revenue"])
        }
        for row in rows
    ]


# =========================
# PAGE SEGMENTATION RFM
# =========================

@router.get("/gold/rfm/distributions")
def get_rfm_distributions():
    macro_query = text("""
        SELECT
            macro_segment,
            COUNT(*) AS count
        FROM gold.foyer_rfm_segments
        GROUP BY macro_segment
        ORDER BY count DESC
    """)

    recency_query = text("""
        SELECT
            recency_segment,
            COUNT(*) AS count
        FROM gold.foyer_rfm_segments
        GROUP BY recency_segment
        ORDER BY count DESC
    """)

    frequency_query = text("""
        SELECT
            frequency_segment,
            COUNT(*) AS count
        FROM gold.foyer_rfm_segments
        GROUP BY frequency_segment
        ORDER BY count DESC
    """)

    monetary_query = text("""
        SELECT
            monetary_segment,
            COUNT(*) AS count
        FROM gold.foyer_rfm_segments
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
            "count": int(row._mapping["count"])
        }
        for row in macro_rows
    ]

    recency_segments = [
        {
            "recency_segment": row._mapping["recency_segment"],
            "count": int(row._mapping["count"])
        }
        for row in recency_rows
    ]

    frequency_segments = [
        {
            "frequency_segment": row._mapping["frequency_segment"],
            "count": int(row._mapping["count"])
        }
        for row in frequency_rows
    ]

    monetary_segments = [
        {
            "monetary_segment": row._mapping["monetary_segment"],
            "count": int(row._mapping["count"])
        }
        for row in monetary_rows
    ]

    total_foyers = sum(item["count"] for item in macro_segments)

    return {
        "total_foyers": total_foyers,
        "macro_segments": macro_segments,
        "recency_segments": recency_segments,
        "frequency_segments": frequency_segments,
        "monetary_segments": monetary_segments
    }


# =========================
# PAGE RECHERCHE - ANGLE CLIENT
# =========================

@router.get("/search/customer/{customer_id}")
def search_customer(customer_id: str):
    client_query = text("""
        SELECT
            customer_id,
            foyer_id,
            customer_city,
            customer_state
        FROM datamarket.customers
        WHERE customer_id = :customer_id
    """)

    with engine.connect() as connection:
        client_row = connection.execute(
            client_query, {"customer_id": customer_id}
        ).fetchone()

        if client_row is None:
            raise HTTPException(status_code=404, detail="Client introuvable")

        client = dict(client_row._mapping)
        foyer_id = client["foyer_id"]

        foyer_query = text("""
            SELECT
                foyer_id,
                foyer_created_at,
                foyer_status
            FROM datamarket.foyers
            WHERE foyer_id = :foyer_id
        """)

        foyer_row = connection.execute(
            foyer_query, {"foyer_id": foyer_id}
        ).fetchone()

        foyer = dict(foyer_row._mapping) if foyer_row else None

        segmentation_query = text("""
            SELECT
                foyer_id,
                last_purchase_date,
                recency_days,
                frequency,
                monetary,
                recency_segment,
                frequency_segment,
                monetary_segment,
                macro_segment
            FROM gold.foyer_rfm_segments
            WHERE foyer_id = :foyer_id
        """)

        segmentation_row = connection.execute(
            segmentation_query, {"foyer_id": foyer_id}
        ).fetchone()

        foyer_segmentation = (
            dict(segmentation_row._mapping) if segmentation_row else None
        )

        other_clients_query = text("""
            SELECT
                customer_id,
                customer_city,
                customer_state
            FROM datamarket.customers
            WHERE foyer_id = :foyer_id
            ORDER BY customer_id
        """)

        other_clients_rows = connection.execute(
            other_clients_query, {"foyer_id": foyer_id}
        ).fetchall()

        autres_clients_du_foyer = [
            dict(row._mapping) for row in other_clients_rows
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
            transactions_query, {"customer_id": customer_id}
        ).fetchall()

        transactions_du_client = [
            {
                "transaction_id": row._mapping["transaction_id"],
                "transaction_timestamp": row._mapping["transaction_timestamp"],
                "transaction_amount": float(row._mapping["transaction_amount"])
            }
            for row in transactions_rows
        ]

    return {
        "client": client,
        "foyer": foyer,
        "foyer_segmentation": foyer_segmentation,
        "autres_clients_du_foyer": autres_clients_du_foyer,
        "transactions_du_client": transactions_du_client
    }

@router.get("/search/customers")
def list_customers(limit: int = 50):
    query = text("""
        SELECT
            customer_id,
            foyer_id,
            customer_city,
            customer_state
        FROM datamarket.customers
        ORDER BY customer_id
        LIMIT :limit
    """)

    with engine.connect() as connection:
        rows = connection.execute(query, {"limit": limit}).fetchall()

    return [
        {
            "customer_id": row._mapping["customer_id"],
            "foyer_id": row._mapping["foyer_id"],
            "customer_city": row._mapping["customer_city"],
            "customer_state": row._mapping["customer_state"]
        }
        for row in rows
    ]


# =========================
# PAGE RECHERCHE - ANGLE FOYER
# =========================

@router.get("/search/foyer/{foyer_id}")
def search_foyer(foyer_id: str):
    foyer_query = text("""
        SELECT
            foyer_id,
            foyer_created_at,
            foyer_status
        FROM datamarket.foyers
        WHERE foyer_id = :foyer_id
    """)

    with engine.connect() as connection:
        foyer_row = connection.execute(
            foyer_query, {"foyer_id": foyer_id}
        ).fetchone()

        if foyer_row is None:
            raise HTTPException(status_code=404, detail="Foyer introuvable")

        foyer = dict(foyer_row._mapping)

        segmentation_query = text("""
            SELECT
                foyer_id,
                last_purchase_date,
                recency_days,
                frequency,
                monetary,
                recency_segment,
                frequency_segment,
                monetary_segment,
                macro_segment
            FROM gold.foyer_rfm_segments
            WHERE foyer_id = :foyer_id
        """)

        segmentation_row = connection.execute(
            segmentation_query, {"foyer_id": foyer_id}
        ).fetchone()

        foyer_segmentation = (
            dict(segmentation_row._mapping) if segmentation_row else None
        )

        clients_query = text("""
            SELECT
                customer_id,
                customer_city,
                customer_state
            FROM datamarket.customers
            WHERE foyer_id = :foyer_id
            ORDER BY customer_id
        """)

        clients_rows = connection.execute(
            clients_query, {"foyer_id": foyer_id}
        ).fetchall()

        clients_du_foyer = [dict(row._mapping) for row in clients_rows]

        transactions_query = text("""
            SELECT
                ta.transaction_id,
                ta.customer_id,
                ta.transaction_timestamp,
                ta.transaction_amount
            FROM gold.transaction_amount ta
            WHERE ta.foyer_id = :foyer_id
            ORDER BY ta.transaction_timestamp DESC
        """)

        transactions_rows = connection.execute(
            transactions_query, {"foyer_id": foyer_id}
        ).fetchall()

        transactions_du_foyer = [
            {
                "transaction_id": row._mapping["transaction_id"],
                "customer_id": row._mapping["customer_id"],
                "transaction_timestamp": row._mapping["transaction_timestamp"],
                "transaction_amount": float(row._mapping["transaction_amount"])
            }
            for row in transactions_rows
        ]

    return {
        "foyer": foyer,
        "foyer_segmentation": foyer_segmentation,
        "clients_du_foyer": clients_du_foyer,
        "transactions_du_foyer": transactions_du_foyer
    }



@router.get("/search/foyers")
def list_foyers(limit: int = 50):
    query = text("""
        SELECT
            f.foyer_id,
            f.foyer_created_at,
            f.foyer_status
        FROM datamarket.foyers f
        ORDER BY f.foyer_id
        LIMIT :limit
    """)

    with engine.connect() as connection:
        rows = connection.execute(query, {"limit": limit}).fetchall()

    return [
        {
            "foyer_id": row._mapping["foyer_id"],
            "foyer_created_at": row._mapping["foyer_created_at"],
            "foyer_status": row._mapping["foyer_status"]
        }
        for row in rows
    ]