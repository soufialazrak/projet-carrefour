import os
import requests
import pandas as pd
import streamlit as st
from utils.sidebar import sidebar

st.set_page_config(page_title="Recherche", layout="wide")
sidebar("Recherche")

API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000")

# =========================
# STYLE GLOBAL
# =========================
st.markdown("""
<style>

/* ===== TITRE PAGE ===== */
.page-title-small {
    text-align: center;
    color: #004f9f;
    font-size: 52px;
    font-weight: 800;
    margin-bottom: 5px;
}

.page-subtitle-small {
    text-align: center;
    color: #444;
    font-size: 16px;
    margin-bottom: 15px;
}

/* ===== TITRES BLOCS ===== */
.section-title {
    color: #1f2a44;
    font-size: 22px;
    font-weight: 700;
    text-decoration: underline;
    text-align: center;
    font-family: "Times New Roman", serif;
}

/* ===== CARTES ===== */
.block-card {
    background-color: #f7f7f7;
    padding: 18px;
    border-radius: 12px;
    border: 1px solid #e6e6e6;
    margin-bottom: 15px;
}

.info-label {
    font-size: 13px;
    color: #666;
}

.info-value {
    font-size: 18px;
    font-weight: 700;
    color: #1f2a44;
    margin-bottom: 12px;
    word-break: break-word;
}

/* ===== BADGES ===== */
.badge {
    display: inline-block;
    padding: 6px 12px;
    border-radius: 999px;
    font-weight: 700;
    font-size: 14px;
    margin-top: 4px;
}

.badge-or {
    background-color: #fff3cd;
    color: #8a6d00;
    border: 1px solid #e7c766;
}

.badge-argent {
    background-color: #f1f3f5;
    color: #555;
    border: 1px solid #d0d4d9;
}

.badge-bronze {
    background-color: #f7e5d6;
    color: #8a4f20;
    border: 1px solid #cd7f32;
}

.badge-faible-panier {
    background-color: #e8f0ff;
    color: #2f5aa8;
    border: 1px solid #9ab6f0;
}

.badge-gros-panier {
    background-color: #fde8e8;
    color: #b93838;
    border: 1px solid #e15759;
}

.badge-analyser {
    background-color: #eeeeee;
    color: #555;
    border: 1px solid #bbbbbb;
}

/* =========================
   TABS DESIGN PREMIUM
========================= */

div[data-baseweb="tab-list"] {
    width: 100%;
    display: flex;
}

button[data-baseweb="tab"] {
    flex: 1 1 0%;
    justify-content: center;
    font-size: 28px !important;
    font-weight: 900 !important;
    font-family: "Georgia", "Times New Roman", serif !important;
    color: #0046AD !important;
    border-bottom: 3px solid transparent !important;
    padding: 14px 0 !important;
    letter-spacing: 0.3px;
}

/* Onglet actif */
button[aria-selected="true"] {
    color: #d62828 !important;
    border-bottom: 4px solid #d62828 !important;
    font-weight: 900 !important;
}

/* Hover */
button[data-baseweb="tab"]:hover {
    color: #d62828 !important;
}

/* =========================
   BOUTONS
========================= */

/* Boutons "Liste" */
div.stButton > button {
    background: white;
    color: #1f2a44;
    border: 1px solid #d9d9d9;
    border-radius: 8px;
    padding: 8px 14px;
    font-size: 16px;
    font-weight: 600;
}

/* Boutons "Rechercher" */
button[kind="primary"] {
    width: 100% !important;
    background: #e8f0ff !important;
    color: #0046AD !important;
    border: 1px solid #bcd0ff !important;
    border-left: 6px solid #0046AD !important;
    border-radius: 10px !important;
    font-size: 20px !important;
    font-weight: 800 !important;
    padding: 14px !important;
}

/* Hover bouton principal */
button[kind="primary"]:hover {
    background: #dce8ff !important;
    color: #0046AD !important;
    border-color: #9fbcff !important;
    border-left: 6px solid #003a91 !important;
}

</style>
""", unsafe_allow_html=True)

# =========================
# TITRE
# =========================
st.markdown('<div class="page-title-small">Recherche</div>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle-small">Recherche client et foyer</div>', unsafe_allow_html=True)
st.divider()


def get_badge_class(macro_segment: str | None) -> str:
    if macro_segment == "Or":
        return "badge badge-or"
    if macro_segment == "Argent":
        return "badge badge-argent"
    if macro_segment == "Bronze":
        return "badge badge-bronze"
    if macro_segment == "fideles faible panier":
        return "badge badge-faible-panier"
    if macro_segment == "gros panier occasionnel":
        return "badge badge-gros-panier"
    return "badge badge-analyser"


def fetch_json(endpoint: str):
    response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=60)
    response.raise_for_status()
    return response.json()


def render_info_card(title: str, data: dict):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)

    if not data:
        st.info("Aucune donnée disponible.")
        return

    st.markdown('<div class="block-card">', unsafe_allow_html=True)

    cols = st.columns(2)
    items = list(data.items())

    for i, (key, value) in enumerate(items):
        with cols[i % 2]:
            st.markdown(f'<div class="info-label">{key}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="info-value">{value}</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


def render_segmentation_card(segmentation: dict):
    st.markdown('<div class="section-title">Segmentation RFM</div>', unsafe_allow_html=True)

    if not segmentation:
        st.info("Aucune segmentation disponible.")
        return

    macro_segment = segmentation.get("macro_segment")
    badge_class = get_badge_class(macro_segment)

    st.markdown('<div class="block-card">', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown('<div class="info-label">Récence (jours)</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="info-value">{segmentation.get("recency_days", "")}</div>', unsafe_allow_html=True)
        st.markdown('<div class="info-label">Segment récence</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="info-value">{segmentation.get("recency_segment", "")}</div>', unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="info-label">Fréquence</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="info-value">{segmentation.get("frequency", "")}</div>', unsafe_allow_html=True)
        st.markdown('<div class="info-label">Segment fréquence</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="info-value">{segmentation.get("frequency_segment", "")}</div>', unsafe_allow_html=True)

    with c3:
        st.markdown('<div class="info-label">Montant</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="info-value">{segmentation.get("monetary", "")}</div>', unsafe_allow_html=True)
        st.markdown('<div class="info-label">Segment montant</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="info-value">{segmentation.get("monetary_segment", "")}</div>', unsafe_allow_html=True)

    with c4:
        st.markdown('<div class="info-label">Dernier achat</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="info-value">{segmentation.get("last_purchase_date", "")}</div>', unsafe_allow_html=True)
        st.markdown('<div class="info-label">Macro segment</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="{badge_class}">{macro_segment}</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


def render_table(title: str, rows):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
    df = pd.DataFrame(rows)
    if df.empty:
        st.info("Aucune donnée disponible.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)


tab_client, tab_foyer = st.tabs(["Recherche par client", "Recherche par foyer"])

# =========================
# ONGLET CLIENT
# =========================
with tab_client:
    col1, col2 = st.columns([2, 1])

    with col1:
        customer_id = st.text_input("ID client", key="customer_id_input")

    with col2:
        show_customer_list = st.button("Liste des clients", use_container_width=True, key="liste_clients")

    if show_customer_list:
        try:
            data = fetch_json("/search/customers")
            render_table("Liste des clients", data)
            st.divider()
        except Exception as e:
            st.error(f"Erreur lors du chargement de la liste des clients : {e}")

    col_btn = st.columns([1, 2, 1])
    with col_btn[1]:
        search_customer = st.button(
            "Rechercher le client",
            type="primary",
            use_container_width=True,
            key="rechercher_client"
        )

    if search_customer:
        if not customer_id:
            st.warning("Veuillez saisir un ID client.")
        else:
            try:
                data = fetch_json(f"/search/customer/{customer_id}")

                st.divider()

                c1, c2 = st.columns(2)

                with c1:
                    render_info_card("Informations client", data["client"])
                    render_info_card("Informations du foyer", data["foyer"])

                with c2:
                    render_segmentation_card(data["foyer_segmentation"])

                render_table("Autres clients du foyer", data["autres_clients_du_foyer"])
                render_table("Transactions du client", data["transactions_du_client"])

            except requests.HTTPError as e:
                if e.response is not None and e.response.status_code == 404:
                    st.error("Client introuvable.")
                else:
                    st.error(f"Erreur API : {e}")
            except Exception as e:
                st.error(f"Erreur : {e}")

# =========================
# ONGLET FOYER
# =========================
with tab_foyer:
    col1, col2 = st.columns([2, 1])

    with col1:
        foyer_id = st.text_input("ID foyer", key="foyer_id_input")

    with col2:
        show_foyer_list = st.button("Liste des foyers", use_container_width=True, key="liste_foyers")

    if show_foyer_list:
        try:
            data = fetch_json("/search/foyers")
            render_table("Liste des foyers", data)
            st.divider()
        except Exception as e:
            st.error(f"Erreur lors du chargement de la liste des foyers : {e}")

    col_btn = st.columns([1, 2, 1])
    with col_btn[1]:
        search_foyer = st.button(
            "Rechercher le foyer",
            type="primary",
            use_container_width=True,
            key="rechercher_foyer"
        )

    if search_foyer:
        if not foyer_id:
            st.warning("Veuillez saisir un ID foyer.")
        else:
            try:
                data = fetch_json(f"/search/foyer/{foyer_id}")

                st.divider()

                c1, c2 = st.columns(2)

                with c1:
                    render_info_card("Informations du foyer", data["foyer"])

                with c2:
                    render_segmentation_card(data["foyer_segmentation"])

                render_table("Clients du foyer", data["clients_du_foyer"])
                render_table("Transactions du foyer", data["transactions_du_foyer"])

            except requests.HTTPError as e:
                if e.response is not None and e.response.status_code == 404:
                    st.error("Foyer introuvable.")
                else:
                    st.error(f"Erreur API : {e}")
            except Exception as e:
                st.error(f"Erreur : {e}")