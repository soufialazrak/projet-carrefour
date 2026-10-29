import os

import altair as alt
import pandas as pd
import requests
import streamlit as st

from utils.sidebar import sidebar


st.set_page_config(
    page_title="Streaming Kafka",
    layout="wide"
)

sidebar("Streaming")

API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000")

st.markdown(
    "<h1 style='text-align:center;color:#0046AD;'>Streaming Kafka</h1>",
    unsafe_allow_html=True
)

st.markdown(
    "<p style='text-align:center;'>"
    "Suivi des transactions simulees : Kafka, MinIO, PostgreSQL et FastAPI"
    "</p>",
    unsafe_allow_html=True
)

st.info(
    "Les transactions de cette page sont des evenements synthetiques "
    "distincts des donnees historiques utilisees pour la segmentation RFM."
)

st.divider()

col_limit, col_page = st.columns(2)

with col_limit:
    limit = st.selectbox(
        "Transactions par page",
        options=[10, 50, 100, 500],
        index=1
    )

with col_page:
    page = st.number_input(
        "Numero de page",
        min_value=1,
        value=1,
        step=1
    )

offset = (page - 1) * limit

if st.button("Actualiser les donnees"):
    st.rerun()

try:
    response = requests.get(
        f"{API_BASE_URL}/streaming/transactions",
        params={"limit": limit, "offset": offset},
        timeout=30
    )
    response.raise_for_status()

    payload = response.json()
    total = int(payload.get("total", 0))
    transactions = payload.get("transactions", [])

    df = pd.DataFrame(transactions)

    st.subheader("Indicateurs streaming")

    col1, col2, col3 = st.columns(3)

    col1.metric("Transactions totales", f"{total:,}".replace(",", " "))
    col2.metric("Transactions affichees", len(df))

    montant_page = (
        float(df["amount"].sum())
        if not df.empty and "amount" in df.columns
        else 0.0
    )

    col3.metric(
        "Montant de la page",
        f"{montant_page:,.2f} EUR".replace(",", " ")
    )

    st.caption(
        "Le montant correspond uniquement aux transactions de la page "
        "affichee, et non a l'ensemble de la base."
    )

    st.divider()

    if df.empty:
        st.info("Aucune transaction disponible pour cette page.")

    else:
        st.subheader("Repartition par canal")

        repartition = (
            df.groupby("channel", as_index=False)
            .agg(
                transactions=("transaction_id", "count"),
                montant=("amount", "sum")
            )
        )

        chart = (
            alt.Chart(repartition)
            .mark_bar(color="#0046AD")
            .encode(
                x=alt.X("channel:N", title="Canal"),
                y=alt.Y("transactions:Q", title="Nombre de transactions"),
                tooltip=[
                    alt.Tooltip("channel:N", title="Canal"),
                    alt.Tooltip("transactions:Q", title="Transactions"),
                    alt.Tooltip("montant:Q", title="Montant EUR", format=".2f")
                ]
            )
            .properties(height=300)
        )

        st.altair_chart(chart, use_container_width=True)

        st.divider()
        st.subheader("Transactions Kafka")

        colonnes = [
            "transaction_id",
            "event_timestamp",
            "amount",
            "currency",
            "channel",
            "source",
            "ingested_at",
            "event_id"
        ]

        st.dataframe(
            df[colonnes],
            use_container_width=True,
            hide_index=True
        )

    st.caption(
        f"Pagination : page {page} | "
        f"total {total} transactions | "
        f"limite {limit}"
    )

except requests.exceptions.RequestException as exc:
    st.error(f"Impossible de recuperer les transactions via FastAPI : {exc}")

except Exception as exc:
    st.error(f"Erreur lors de l'affichage des transactions : {exc}")