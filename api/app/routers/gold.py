from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text
from app.db import engine

router = APIRouter()


@router.get("/gold/transaction-amount")
def get_transaction_amount(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    query = text("""
        SELECT
            transaction_id,
            customer_id,
            foyer_id,
            transaction_timestamp,
            transaction_amount
        FROM gold.transaction_amount
        ORDER BY transaction_timestamp DESC
        LIMIT :limit OFFSET :offset
    """)

    count_query = text("""
        SELECT COUNT(*) AS total
        FROM gold.transaction_amount
    """)

    with engine.connect() as connection:
        result = connection.execute(query, {"limit": limit, "offset": offset})
        data = [dict(row._mapping) for row in result]

        total = connection.execute(count_query).scalar()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "data": data
    }


@router.get("/gold/transaction-amount/{transaction_id}")
def get_transaction_amount_by_id(transaction_id: str):
    query = text("""
        SELECT
            transaction_id,
            customer_id,
            foyer_id,
            transaction_timestamp,
            transaction_amount
        FROM gold.transaction_amount
        WHERE transaction_id = :transaction_id
    """)

    with engine.connect() as connection:
        result = connection.execute(query, {"transaction_id": transaction_id})
        row = result.fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Transaction gold introuvable")

    return dict(row._mapping)


@router.get("/gold/foyer-rfm-metrics")
def get_foyer_rfm_metrics(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    query = text("""
        SELECT
            foyer_id,
            last_purchase_date,
            recency_days,
            frequency,
            monetary
        FROM gold.foyer_rfm_metrics
        ORDER BY monetary DESC
        LIMIT :limit OFFSET :offset
    """)

    count_query = text("""
        SELECT COUNT(*) AS total
        FROM gold.foyer_rfm_metrics
    """)

    with engine.connect() as connection:
        result = connection.execute(query, {"limit": limit, "offset": offset})
        data = [dict(row._mapping) for row in result]

        total = connection.execute(count_query).scalar()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "data": data
    }


@router.get("/gold/foyer-rfm-metrics/{foyer_id}")
def get_foyer_rfm_metrics_by_foyer_id(foyer_id: str):
    query = text("""
        SELECT
            foyer_id,
            last_purchase_date,
            recency_days,
            frequency,
            monetary
        FROM gold.foyer_rfm_metrics
        WHERE foyer_id = :foyer_id
    """)

    with engine.connect() as connection:
        result = connection.execute(query, {"foyer_id": foyer_id})
        row = result.fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="RFM metrics introuvables pour ce foyer")

    return dict(row._mapping)


@router.get("/gold/foyer-rfm-segments")
def get_foyer_rfm_segments(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    macro_segment: str | None = Query(default=None)
):
    if macro_segment:
        query = text("""
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
            WHERE macro_segment = :macro_segment
            ORDER BY monetary DESC
            LIMIT :limit OFFSET :offset
        """)

        count_query = text("""
            SELECT COUNT(*) AS total
            FROM gold.foyer_rfm_segments
            WHERE macro_segment = :macro_segment
        """)

        params = {
            "macro_segment": macro_segment,
            "limit": limit,
            "offset": offset
        }

        count_params = {
            "macro_segment": macro_segment
        }
    else:
        query = text("""
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
            ORDER BY monetary DESC
            LIMIT :limit OFFSET :offset
        """)

        count_query = text("""
            SELECT COUNT(*) AS total
            FROM gold.foyer_rfm_segments
        """)

        params = {
            "limit": limit,
            "offset": offset
        }

        count_params = {}

    with engine.connect() as connection:
        result = connection.execute(query, params)
        data = [dict(row._mapping) for row in result]

        total = connection.execute(count_query, count_params).scalar()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "macro_segment": macro_segment,
        "data": data
    }


@router.get("/gold/foyer-rfm-segments/{foyer_id}")
def get_foyer_rfm_segments_by_foyer_id(foyer_id: str):
    query = text("""
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

    with engine.connect() as connection:
        result = connection.execute(query, {"foyer_id": foyer_id})
        row = result.fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Segmentation RFM introuvable pour ce foyer")

    return dict(row._mapping)


@router.get("/gold/customer-value")
def get_customer_value(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    query = text("""
        SELECT
            customer_id,
            nb_transactions,
            total_spent,
            avg_item_price
        FROM gold.customer_value
        ORDER BY total_spent DESC NULLS LAST
        LIMIT :limit OFFSET :offset
    """)

    count_query = text("""
        SELECT COUNT(*) AS total
        FROM gold.customer_value
    """)

    with engine.connect() as connection:
        result = connection.execute(query, {"limit": limit, "offset": offset})
        data = [dict(row._mapping) for row in result]

        total = connection.execute(count_query).scalar()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "data": data
    }


@router.get("/gold/customer-value/{customer_id}")
def get_customer_value_by_customer_id(customer_id: str):
    query = text("""
        SELECT
            customer_id,
            nb_transactions,
            total_spent,
            avg_item_price
        FROM gold.customer_value
        WHERE customer_id = :customer_id
    """)

    with engine.connect() as connection:
        result = connection.execute(query, {"customer_id": customer_id})
        row = result.fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Customer value introuvable pour ce client")

    return dict(row._mapping)


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


@router.get("/gold/rfm/macro-segment-count")
def get_macro_segment_count():
    query = text("""
        SELECT
            macro_segment,
            COUNT(*) AS count
        FROM gold.foyer_rfm_segments
        GROUP BY macro_segment
        ORDER BY count DESC
    """)

    with engine.connect() as connection:
        result = connection.execute(query)
        rows = result.fetchall()

    return [
        {
            "macro_segment": row._mapping["macro_segment"],
            "count": int(row._mapping["count"])
        }
        for row in rows
    ]


@router.get("/gold/rfm/recency-segment-count")
def get_recency_segment_count():
    query = text("""
        SELECT
            recency_segment,
            COUNT(*) AS count
        FROM gold.foyer_rfm_segments
        GROUP BY recency_segment
        ORDER BY count DESC
    """)

    with engine.connect() as connection:
        result = connection.execute(query)
        rows = result.fetchall()

    return [
        {
            "recency_segment": row._mapping["recency_segment"],
            "count": int(row._mapping["count"])
        }
        for row in rows
    ]


@router.get("/gold/rfm/frequency-segment-count")
def get_frequency_segment_count():
    query = text("""
        SELECT
            frequency_segment,
            COUNT(*) AS count
        FROM gold.foyer_rfm_segments
        GROUP BY frequency_segment
        ORDER BY count DESC
    """)

    with engine.connect() as connection:
        result = connection.execute(query)
        rows = result.fetchall()

    return [
        {
            "frequency_segment": row._mapping["frequency_segment"],
            "count": int(row._mapping["count"])
        }
        for row in rows
    ]


@router.get("/gold/rfm/monetary-segment-count")
def get_monetary_segment_count():
    query = text("""
        SELECT
            monetary_segment,
            COUNT(*) AS count
        FROM gold.foyer_rfm_segments
        GROUP BY monetary_segment
        ORDER BY count DESC
    """)

    with engine.connect() as connection:
        result = connection.execute(query)
        rows = result.fetchall()

    return [
        {
            "monetary_segment": row._mapping["monetary_segment"],
            "count": int(row._mapping["count"])
        }
        for row in rows
    ]