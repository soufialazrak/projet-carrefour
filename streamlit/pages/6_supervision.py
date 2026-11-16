import base64
import mimetypes
from html import escape
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from utils.sidebar import sidebar


st.set_page_config(
    page_title="Supervision | DataMarket Carrefour",
    layout="wide",
    initial_sidebar_state="expanded",
)
sidebar("Supervision")

STREAMLIT_ROOT = Path(__file__).resolve().parents[1]
LOGOS_DIR = STREAMLIT_ROOT / "assets" / "logos"

st.markdown(
    """
    <style>
    .page-title-small {
        text-align: center;
        color: #004f9f;
        font-size: 52px;
        font-weight: 800;
        margin-top: 0;
        margin-bottom: 2px;
    }
    .page-subtitle-small {
        text-align: center;
        color: #444;
        font-size: 16px;
        margin-bottom: 10px;
    }
    .section-title {
        color: #1f2a44;
        font-size: 22px;
        font-weight: 700;
        text-decoration: underline;
        margin-bottom: 8px;
        text-align: center;
        font-family: "Times New Roman", Times, serif;
    }
    .chart-title, .table-heading {
        color: #1f2a44;
        font-size: 20px;
        font-weight: 700;
        text-decoration: underline;
        margin-bottom: 12px;
        text-align: center;
        font-family: "Times New Roman", Times, serif;
    }
    .insight-box {
        background-color: #f7f7f7;
        padding: 12px 14px;
        border-radius: 10px;
        border-left: 5px solid #004f9f;
        font-size: 14px;
        color: #1f2a44;
        margin-top: 8px;
        line-height: 1.6;
    }
    .kpi-circle {
        width: 220px;
        height: 220px;
        border: 4px solid #d62828;
        border-radius: 50%;
        background-color: #fffafa;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        margin: 16px auto;
        padding: 16px;
        box-sizing: border-box;
    }
    .kpi-circle-label {
        font-family: "Times New Roman", Times, serif;
        font-size: 19px;
        font-weight: 700;
        text-decoration: underline;
        color: #1f2a44;
        line-height: 1.3;
        margin-bottom: 12px;
    }
    .kpi-circle-value {
        font-family: Arial, sans-serif;
        font-size: 28px;
        font-weight: 800;
        color: #1f2a44;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def component_header(name: str, filename: str, description: str) -> None:
    """Logos affichés dans une zone de taille homogène, sans déformation."""
    logo_col, title_col = st.columns([1, 7], gap="small", vertical_alignment="center")
    with logo_col:
        logo_path = LOGOS_DIR / filename
        if logo_path.is_file():
            mime_type = mimetypes.guess_type(logo_path.name)[0] or "image/png"
            logo_data = base64.b64encode(logo_path.read_bytes()).decode("ascii")
            st.markdown(
                f'<div style="width:75px;height:75px;display:flex;align-items:center;'
                f'justify-content:center;">'
                f'<img src="data:{mime_type};base64,{logo_data}" '
                f'style="max-width:75px;max-height:75px;object-fit:contain;" '
                f'alt="Logo {escape(name)}"></div>',
                unsafe_allow_html=True,
            )
        else:
            st.caption("Logo absent")
    with title_col:
        st.markdown(
            f'<div class="section-title">{escape(name)}</div>',
            unsafe_allow_html=True,
        )
        st.caption(description)


def insight_box(message: str) -> None:
    st.markdown(f'<div class="insight-box">{message}</div>', unsafe_allow_html=True)


def kpi_circle(label: str, value: str) -> None:
    st.markdown(
        f'<div class="kpi-circle">'
        f'<div class="kpi-circle-label">{escape(label)}</div>'
        f'<div class="kpi-circle-value">{escape(value)}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


st.markdown(
    '<div class="page-title-small">Supervision du Data Lake</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="page-subtitle-small">Carrefour Data Market | Compétence C19</div>',
    unsafe_allow_html=True,
)

# ============================================================
# 1. DOCKER — cercle à gauche, détail des conteneurs à droite
# ============================================================
with st.container(border=True):
    component_header("Docker", "docker.png", "Ressources et état des conteneurs")
    st.divider()

    docker_details = pd.DataFrame(
        {
            "Conteneur": [
                "Airflow", "Airflow DB", "Redpanda", "PostgreSQL",
                "MinIO", "Streamlit", "FastAPI",
            ],
            "État au contrôle": ["Actif"] * 7,
            "CPU (%)": [4.13, 1.86, 0.38, 0.00, 0.05, 0.30, 0.69],
            "RAM (Mio)": [1146.88, 52.81, 181.10, 147.40, 122.40, 174.40, 78.87],
        }
    )

    docker_kpi, docker_table = st.columns([1, 2], gap="large", vertical_alignment="center")
    with docker_kpi:
        kpi_circle("Mémoire observée", "1,86 Gio")
        st.markdown("<div style='text-align:center;'>Conteneurs observés : <b>7</b></div>", unsafe_allow_html=True)
    with docker_table:
        st.markdown('<div class="table-heading">Détail des 7 conteneurs</div>', unsafe_allow_html=True)
        st.dataframe(
            docker_details,
            use_container_width=True,
            hide_index=True,
            height=300,
            column_config={
                "Conteneur": st.column_config.TextColumn("Conteneur"),
                "État au contrôle": st.column_config.TextColumn("État au contrôle"),
                "CPU (%)": st.column_config.NumberColumn("CPU (%)", format="%.2f"),
                "RAM (Mio)": st.column_config.NumberColumn("RAM (Mio)", format="%.2f"),
            },
        )
    insight_box(
        "Les <b>7 conteneurs</b> étaient actifs lors du dernier contrôle. "
        "Les valeurs CPU et RAM sont <b>historiques</b> et non actualisées en temps réel."
    )


# ============================================================
# 2. MINIO — informations à gauche, camembert à droite
# ============================================================
with st.container(border=True):
    minio_infos, minio_graph = st.columns([1, 1.2], gap="large", vertical_alignment="top")

    with minio_infos:
        component_header("MinIO", "minio.png", "Stockage objet Bronze et Silver")
        st.divider()
        volume_col, http_col = st.columns(2)
        with volume_col:
            st.metric("Volume physique relevé", "124 Mio")
        with http_col:
            st.metric("Dernier code HTTP", "200")
        insight_box(
            "Le code <b>HTTP 200</b> indique que MinIO a répondu correctement "
            "au contrôle de disponibilité <b>/minio/health/live</b>. "
            "Ce résultat correspond au moment du dernier test."
        )

    with minio_graph:
        st.markdown(
            '<div class="chart-title">Répartition du stockage MinIO</div>',
            unsafe_allow_html=True,
        )
        stockage = pd.DataFrame(
            {"Zone": ["Bronze", "Silver"], "Volume (Mio)": [48, 76]}
        )
        stockage["Pourcentage"] = stockage["Volume (Mio)"] / stockage["Volume (Mio)"].sum() * 100
        stockage["Étiquette"] = stockage["Pourcentage"].map(
            lambda valeur: f"{valeur:.1f} %".replace(".", ",")
        )

        secteurs = (
            alt.Chart(stockage)
            .mark_arc()
            .encode(
                theta=alt.Theta("Volume (Mio):Q", stack=True),
                color=alt.Color(
                    "Zone:N",
                    scale=alt.Scale(
                        domain=["Bronze", "Silver"],
                        range=["#C47A36", "#A0A8B5"],
                    ),
                    legend=alt.Legend(title="Couche", orient="right"),
                ),
                order=alt.Order("Zone:N", sort="ascending"),
                tooltip=[
                    alt.Tooltip("Zone:N", title="Couche"),
                    alt.Tooltip("Volume (Mio):Q", title="Volume (Mio)"),
                    alt.Tooltip("Pourcentage:Q", title="Part (%)", format=".1f"),
                ],
            )
        )
        pourcentages = (
            alt.Chart(stockage)
            .mark_text(radius=85, fontSize=16, fontWeight="bold", color="white")
            .encode(
                theta=alt.Theta("Volume (Mio):Q", stack=True),
                order=alt.Order("Zone:N", sort="ascending"),
                text=alt.Text("Étiquette:N"),
            )
        )
        graphique_minio = (secteurs + pourcentages).properties(height=310).configure_view(strokeWidth=0)
        st.altair_chart(graphique_minio, use_container_width=True)
        st.caption("Bronze : 48 Mio (38,7 %) | Silver : 76 Mio (61,3 %)")


# ============================================================
# 3. POSTGRESQL — cercle à gauche, tableau à droite
# ============================================================
with st.container(border=True):
    component_header("PostgreSQL", "postgresql.jpg", "Volumes des tables du Data Market")
    st.divider()

    tables = pd.DataFrame(
        {
            "Table": [
                "product_categories", "products", "households", "loyalty_cards",
                "customers", "transactions", "transaction_items",
            ],
            "Enregistrements": [74, 32951, 44237, 99438, 96096, 99441, 112650],
        }
    )
    total = f"{int(tables['Enregistrements'].sum()):,}".replace(",", " ")
    pg_kpi, pg_table = st.columns([1, 2], gap="large", vertical_alignment="center")
    with pg_kpi:
        kpi_circle("Total des enregistrements", total)
    with pg_table:
        st.markdown('<div class="table-heading">Détail des tables PostgreSQL</div>', unsafe_allow_html=True)
        st.dataframe(
            tables,
            use_container_width=True,
            hide_index=True,
            height=300,
            column_config={
                "Table": st.column_config.TextColumn("Table"),
                "Enregistrements": st.column_config.NumberColumn("Enregistrements", format="%d"),
            },
        )


# ============================================================
# 4 et 5. AIRFLOW / REDPANDA — côte à côte
# ============================================================
airflow_col, redpanda_col = st.columns(2, gap="medium")

with airflow_col:
    with st.container(border=True):
        component_header("Apache Airflow", "airflow.png", "Orchestration du pipeline Streaming")
        st.divider()
        st.markdown("DAG : `carrefour_streaming_e7`")
        insight_box("Dernière exécution vérifiée : <b>5 tâches réussies</b>.")
        st.caption("Résultat historique, non connecté à Airflow en direct.")

with redpanda_col:
    with st.container(border=True):
        component_header("Redpanda", "redpanda.png", "Streaming compatible Kafka")
        st.divider()
        st.markdown("Topic : `phenix.transactions.e7`")
        insight_box("État du broker : <b>à connecter à la collecte de supervision</b>.")
