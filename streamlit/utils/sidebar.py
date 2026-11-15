
import streamlit as st
import pandas as pd
import altair as alt

from pathlib import Path
from utils.sidebar import sidebar


# ============================================================
# 1. CONFIGURATION DE LA PAGE
# ============================================================

st.set_page_config(
    page_title="Supervision | DataMarket Carrefour",
    layout="wide",
    initial_sidebar_state="expanded"
)

sidebar("Supervision")

# Chemin compatible avec Docker et Windows
STREAMLIT_ROOT = Path(__file__).resolve().parents[1]
LOGOS_DIR = STREAMLIT_ROOT / "assets" / "logos"


# ============================================================
# 2. FONCTION POUR AFFICHER LES LOGOS
# ============================================================

def component_header(name, filename, description):
    col_logo, col_text = st.columns([1, 9])

    with col_logo:
        logo_path = LOGOS_DIR / filename

        if logo_path.exists():
            st.image(str(logo_path), width=55)
        else:
            st.warning("Logo absent")

    with col_text:
        st.subheader(name)
        st.caption(description)


# ============================================================
# 3. TITRE PRINCIPAL
# ============================================================

st.title("Supervision du Data Lake")

st.caption(
    "Carrefour Data Market | Compétence C19"
)

st.info(
    "Ce tableau de bord présente les résultats des derniers "
    "contrôles techniques réalisés sur l'environnement local. "
    "Les indicateurs ne sont pas encore actualisés automatiquement."
)


# ============================================================
# 4. DOCKER - SUPERVISION DES CONTENEURS
# ============================================================

with st.container(border=True):

    component_header(
        "Docker",
        "docker.png",
        "Ressources et état des conteneurs"
    )

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            label="Mémoire RAM observée",
            value="1,86 Gio"
        )

    with col2:
        st.metric(
            label="Conteneurs observés",
            value="7"
        )

    with st.expander("Voir les ressources par conteneur"):

        docker_data = pd.DataFrame({
            "Conteneur": [
                "Airflow",
                "Airflow PostgreSQL",
                "Redpanda",
                "PostgreSQL DataMarket",
                "MinIO",
                "Streamlit",
                "FastAPI"
            ],
            "CPU (%)": [
                4.13,
                1.86,
                0.38,
                0.00,
                0.05,
                0.30,
                0.69
            ],
            "RAM (Mio)": [
                1146.88,
                52.81,
                181.10,
                147.40,
                122.40,
                174.40,
                78.87
            ]
        })

        st.dataframe(
            docker_data,
            use_container_width=True,
            hide_index=True
        )

        st.caption(
            "Mesures issues de docker stats --no-stream. "
            "Il s'agit d'un relevé ponctuel."
        )


# ============================================================
# 5. MINIO - STOCKAGE ET DISPONIBILITE
# ============================================================

with st.container(border=True):

    component_header(
        "MinIO",
        "minio.png",
        "Stockage objet des couches Bronze et Silver"
    )

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            label="Volume physique total relevé",
            value="124 Mio"
        )

    with col2:
        st.metric(
            label="Dernier code HTTP",
            value="200"
        )

        with st.popover("ℹ️ Que signifie HTTP 200 ?"):
            st.write(
                "Le code HTTP 200 indique que le service MinIO "
                "a répondu correctement à la requête de contrôle "
                "/minio/health/live."
            )

            st.success(
                "MinIO était disponible au moment du test."
            )

            st.caption(
                "Ce contrôle ponctuel ne garantit pas "
                "la disponibilité permanente du service."
            )

    st.divider()

    st.subheader("Répartition du stockage MinIO")

    stockage = pd.DataFrame({
        "Zone": ["Bronze", "Silver"],
        "Volume (Mio)": [48, 76]
    })

    stockage["Pourcentage"] = (
        stockage["Volume (Mio)"]
        / stockage["Volume (Mio)"].sum()
        * 100
    )

    camembert = (
        alt.Chart(stockage)
        .mark_arc()
        .encode(
            theta=alt.Theta(
                "Volume (Mio):Q",
                title="Volume (Mio)"
            ),
            color=alt.Color(
                "Zone:N",
                scale=alt.Scale(
                    domain=["Bronze", "Silver"],
                    range=["#C47A36", "#A0A8B5"]
                ),
                legend=alt.Legend(title="Couche")
            ),
            tooltip=[
                alt.Tooltip(
                    "Zone:N",
                    title="Couche"
                ),
                alt.Tooltip(
                    "Volume (Mio):Q",
                    title="Volume",
                    format=".1f"
                ),
                alt.Tooltip(
                    "Pourcentage:Q",
                    title="Pourcentage",
                    format=".1f"
                )
            ]
        )
        .properties(
            height=300
        )
    )

    st.altair_chart(
        camembert,
        use_container_width=True
    )

    col_bronze, col_silver = st.columns(2)

    col_bronze.metric(
        "Bronze",
        "48 Mio"
    )

    col_silver.metric(
        "Silver",
        "76 Mio"
    )

    st.caption(
        "Volumes issus des commandes mc du exécutées "
        "sur les répertoires physiques MinIO. "
        "Ils ne correspondent pas uniquement aux "
        "29 objets logiques du catalogue."
    )


# ============================================================
# 6. POSTGRESQL - TABLES ET ENREGISTREMENTS
# ============================================================

with st.container(border=True):

    component_header(
        "PostgreSQL",
        "postgresql.jpg",
        "Volumes des tables du Data Market"
    )

    tables = pd.DataFrame({
        "Table": [
            "product_categories",
            "products",
            "households",
            "loyalty_cards",
            "customers",
            "transactions",
            "transaction_items"
        ],
        "Enregistrements": [
            74,
            32951,
            44237,
            99438,
            96096,
            99441,
            112650
        ]
    })

    total = int(tables["Enregistrements"].sum())

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            label="Tables métier",
            value=len(tables)
        )

    with col2:
        st.metric(
            label="Total des enregistrements",
            value=f"{total:,}".replace(",", " ")
        )

    st.subheader("Détail des tables PostgreSQL")

    st.dataframe(
        tables,
        use_container_width=True,
        hide_index=True
    )

    st.caption(
        "Nombre d'enregistrements relevé lors des "
        "vérifications du chargement Batch. "
        "Ces valeurs ne sont pas encore actualisées "
        "automatiquement."
    )


# ============================================================
# 7. AIRFLOW - ORCHESTRATION
# ============================================================

with st.container(border=True):

    component_header(
        "Apache Airflow",
        "airflow.png",
        "Orchestration du pipeline Streaming"
    )

    st.write(
        "**DAG :** `carrefour_streaming_e7`"
    )

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            label="Tâches du DAG",
            value="5"
        )

    with col2:
        st.metric(
            label="Tâches réussies lors du dernier contrôle",
            value="5 / 5"
        )

    st.success(
        "Les cinq tâches étaient terminées avec succès "
        "lors de la dernière vérification."
    )

    st.caption(
        "État historique vérifié dans l'interface Airflow. "
        "La page n'interroge pas encore l'API Airflow."
    )


# ============================================================
# 8. REDPANDA - STREAMING
# ============================================================

with st.container(border=True):

    component_header(
        "Redpanda",
        "redpanda.png",
        "Broker de streaming compatible Kafka"
    )

    st.write(
        "**Topic :** `phenix.transactions.e7`"
    )

    st.write(
        "**Conteneur :** `phenix_redpanda_e7`"
    )

    st.info(
        "Le broker était actif lors du dernier "
        "contrôle Docker. Les métriques de streaming "
        "ne sont pas encore collectées automatiquement."
    )


# ============================================================
# 9. CONCLUSION
# ============================================================

st.divider()

st.caption(
    "Carrefour Data Market | Supervision technique C19 | "
    "Version initiale basée sur des relevés ponctuels"
)
