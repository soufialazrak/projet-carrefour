import os
import requests
import pandas as pd
import altair as alt
import streamlit as st
from utils.sidebar import sidebar

st.set_page_config(
    page_title="Vue d'ensemble",
    layout="wide"
)

sidebar("Vue")

API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000")


def format_int(value):
    try:
        return f"{int(value):,}".replace(",", " ")
    except Exception:
        return "0"


def format_currency(value):
    try:
        return f"{float(value):,.2f} €".replace(",", " ")
    except Exception:
        return "0,00 €"


# =========================
# STYLE LOCAL DE LA PAGE
# =========================
st.markdown("""
<style>

.title {
    text-align: center;
    color: #004f9f;
    font-size: 46px;
    font-weight: 800;
    margin-bottom: 6px;
    font-family: "Times New Roman", Times, serif;
}

.subtitle {
    text-align: center;
    color: #444;
    font-size: 18px;
    margin-bottom: 18px;
}

.section-title {
    color: #004f9f !important;
    font-size: 24px !important;
    font-weight: 800 !important;
    text-align: center !important;
    font-family: "Times New Roman", serif !important;
    margin-bottom: 20px !important;
    text-decoration: underline !important;
}

.kpi-wrapper {
    display: flex;
    justify-content: center;
    margin-top: 10px;
    margin-bottom: 10px;
}

.kpi-circle {
    width: 220px;
    height: 220px;
    border: 4px solid #d62828;
    border-radius: 50%;
    background-color: #fffdfd;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    box-shadow: 0 2px 10px rgba(0,0,0,0.06);
    text-align: center;
    padding: 18px;
}

.kpi-title {
    font-size: 20px;
    font-weight: 700;
    text-decoration: underline;
    color: #1f2a44;
    margin-bottom: 14px;
    font-family: "Times New Roman", Times, serif;
}

.kpi-value {
    font-size: 28px;
    font-weight: 800;
    color: #1f2a44;
    line-height: 1.2;
}

.chart-box {
    background-color: #f7f7f7;
    padding: 20px;
    border-radius: 14px;
    border: 1px solid #e6e6e6;
}

</style>
""", unsafe_allow_html=True)

# =========================
# TITRE
# =========================
st.markdown('<div class="title">Vue d’ensemble</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Indicateurs clés des données clients</div>',
    unsafe_allow_html=True
)

st.divider()

# =========================
# KPI
# =========================
try:
    response = requests.get(f"{API_BASE_URL}/gold/kpis", timeout=30)
    response.raise_for_status()
    data = response.json()

    nb_clients = data.get("nombre_clients", 0)
    nb_households = data.get("nombre_households", 0)
    nb_transactions = data.get("nombre_transactions", 0)
    ca_total = data.get("chiffre_affaires_total", 0)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="kpi-wrapper">
            <div class="kpi-circle">
                <div class="kpi-title">Nombre de clients</div>
                <div class="kpi-value">{format_int(nb_clients)}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="kpi-wrapper">
            <div class="kpi-circle">
                <div class="kpi-title">Nombre de foyers</div>
                <div class="kpi-value">{format_int(nb_households)}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="kpi-wrapper">
            <div class="kpi-circle">
                <div class="kpi-title">Volume d'achat</div>
                <div class="kpi-value">{format_int(nb_transactions)}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="kpi-wrapper">
            <div class="kpi-circle">
                <div class="kpi-title">Chiffre d'affaires total</div>
                <div class="kpi-value">{format_currency(ca_total)}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

except requests.exceptions.HTTPError as e:
    st.error(f"Erreur HTTP lors du chargement des KPI : {e}")
except requests.exceptions.ConnectionError:
    st.error("Impossible de contacter l'API pour charger les KPI.")
except requests.exceptions.Timeout:
    st.error("Le chargement des KPI a expiré.")
except Exception as e:
    st.error(f"Erreur de chargement des KPI : {e}")

# =========================
# EVOLUTION DU CA PAR MOIS
# =========================
st.divider()

st.markdown(
    """
    <div style="text-align:center;margin-bottom:15px;">
        <span class="kpi-title">
        Évolution du chiffre d'affaires dans le temps
        </span>
    </div>
    """,
    unsafe_allow_html=True
)

try:
    response = requests.get(f"{API_BASE_URL}/gold/revenue_over_time", timeout=30)
    response.raise_for_status()
    revenue_data = response.json()

    df = pd.DataFrame(revenue_data)

    if df.empty:
        st.info("Aucune donnée disponible pour l'évolution du chiffre d'affaires.")
    else:
        if "month" not in df.columns or "revenue" not in df.columns:
            st.error("La réponse API ne contient pas les colonnes attendues : 'month' et 'revenue'.")
        else:
            df["month"] = pd.to_datetime(df["month"], errors="coerce")
            df["revenue"] = pd.to_numeric(df["revenue"], errors="coerce")
            df = df.dropna(subset=["month", "revenue"]).sort_values("month")

            if df.empty:
                st.info("Les données reçues sont vides après nettoyage.")
            else:
                chart = (
                    alt.Chart(df)
                    .mark_line(color="#004f9f", strokeWidth=3)
                    .encode(
                        x=alt.X(
                            "month:T",
                            title="Mois",
                            axis=alt.Axis(format="%Y-%m", labelAngle=-40)
                        ),
                        y=alt.Y("revenue:Q", title="Chiffre d'affaires"),
                        tooltip=[
                            alt.Tooltip("month:T", title="Mois", format="%Y-%m"),
                            alt.Tooltip("revenue:Q", title="Chiffre d'affaires", format=",.2f")
                        ]
                    )
                    .properties(height=420)
                    .interactive()
                )

                points = (
                    alt.Chart(df)
                    .mark_circle(color="#d62828", size=45)
                    .encode(
                        x="month:T",
                        y="revenue:Q",
                        tooltip=[
                            alt.Tooltip("month:T", title="Mois", format="%Y-%m"),
                            alt.Tooltip("revenue:Q", title="Chiffre d'affaires", format=",.2f")
                        ]
                    )
                )

                st.markdown('<div class="chart-box">', unsafe_allow_html=True)
                st.altair_chart(chart + points, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

except requests.exceptions.HTTPError as e:
    st.error(f"Erreur HTTP lors du chargement de l'évolution du CA : {e}")
except requests.exceptions.ConnectionError:
    st.error("Impossible de contacter l'API pour charger l'évolution du chiffre d'affaires.")
except requests.exceptions.Timeout:
    st.error("Le chargement de l'évolution du chiffre d'affaires a expiré.")
except Exception as e:
    st.error(f"Erreur de chargement des données : {e}")