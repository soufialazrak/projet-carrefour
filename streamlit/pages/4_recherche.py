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

/* ===== CONTENEUR SECTION ===== */
.section-container {
    margin-top: 20px;
    margin-bottom: 30px;
}

/* ===== TITRES BLOCS ===== */
.section-title {
    color: #004f9f !important;
    font-size: 24px !important;
    font-weight: 800 !important;
    text-align: center !important;
    font-family: "Times New Roman", serif !important;
    margin-bottom: 20px !important;
    text-decoration: underline !important;
}

/* ===== CARTES ===== */
.block-card {
    background-color: #ffffff;
    padding: 22px 20px;
    border-radius: 14px;
    border: 1px solid #e6e6e6;
    margin-bottom: 25px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.04);
}

.info-label {
    font-size: 13px;
    color: #666;
}

.info-value {
    font-size: 18px;
    font-weight: 700;
    color: #0d1b2a;
    margin-bottom: 14px;
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

.badge-premium {
    background-color: #fff3cd;
    color: #8a6d00;
    border: 1px solid #e7c766;
}

.badge-fort-potentiel {
    background-color: #efe8ff;
    color: #6f42c1;
    border: 1px solid #c9b3ff;
}

.badge-fideles {
    background-color: #e6f7f4;
    color: #1f7a6e;
    border: 1px solid #9fd9cf;
}

.badge-standard {
    background-color: #e8f0ff;
    color: #2f5aa8;
    border: 1px solid #9ab6f0;
}

.badge-reactiver {
    background-color: #fff1e6;
    color: #c46a1a;
    border: 1px solid #f4c08d;
}

.badge-perdus {
    background-color: #fde8e8;
    color: #b93838;
    border: 1px solid #e15759;
}

.badge-default {
    background-color: #eeeeee;
    color: #555;
    border: 1px solid #bbbbbb;
}

/* ===== TABS ===== */
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

button[aria-selected="true"] {
    color: #d62828 !important;
    border-bottom: 4px solid #d62828 !important;
    font-weight: 900 !important;
}

button[data-baseweb="tab"]:hover {
    color: #d62828 !important;
}

/* ===== BOUTONS ===== */
div.stButton > button {
    background: white;
    color: #1f2a44;
    border: 1px solid #d9d9d9;
    border-radius: 8px;
    padding: 8px 14px;
    font-size: 16px;
    font-weight: 600;
}

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

button[kind="primary"]:hover {
    background: #dce8ff !important;
    color: #0046AD !important;
    border-color: #9fbcff !important;
    border-left: 6px solid #003a91 !important;
}
            
div[data-testid="stHorizontalBlock"] > div {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
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
    mapping = {
        "Premium": "badge badge-premium",
        "Fort potentiel": "badge badge-fort-potentiel",
        "Fideles": "badge badge-fideles",
        "Standard": "badge badge-standard",
        "A reactiver": "badge badge-reactiver",
        "Perdus": "badge badge-perdus",
    }
    return mapping.get(macro_segment, "badge badge-default")


def fetch_json(endpoint: str, params=None):
    response = requests.get(f"{API_BASE_URL}{endpoint}", params=params, timeout=60)
    response.raise_for_status()
    return response.json()


def select_columns(rows, columns):
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    existing = [col for col in columns if col in df.columns]
    return df[existing]


def merge_household_data(household: dict | None, household_segmentation: dict | None) -> dict:
    merged = {}
    if household:
        merged.update(household)
    if household_segmentation:
        for key, value in household_segmentation.items():
            if key not in merged or merged.get(key) in (None, ""):
                merged[key] = value
    return merged


def render_info_card(title: str, data: dict):
    st.markdown('<div class="section-container">', unsafe_allow_html=True)
    st.markdown(f"<p class='section-title'>{title}</p>", unsafe_allow_html=True)

    if not data:
        st.info("Aucune donnée disponible.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    st.markdown('<div class="block-card">', unsafe_allow_html=True)

    cols = st.columns(2)
    items = list(data.items())

    for i, (key, value) in enumerate(items):
        with cols[i % 2]:
            st.markdown(f'<div class="info-label">{key}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="info-value">{value}</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


def render_household_card(title: str, household_data: dict):
    st.markdown('<div class="section-container">', unsafe_allow_html=True)
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)

    if not household_data:
        st.info("Aucune donnée disponible.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    ordered_keys = [
        "household_id",
        "household_created_at",
        "last_purchase_date",
        "recency_days",
        "frequency",
        "monetary",
        "recency_segment",
        "frequency_segment",
        "monetary_segment",
        "macro_segment",
    ]

    ordered_data = {k: household_data.get(k, "") for k in ordered_keys if k in household_data}

    st.markdown('<div class="block-card">', unsafe_allow_html=True)

    cols = st.columns(2)
    items = list(ordered_data.items())

    for i, (key, value) in enumerate(items):
        with cols[i % 2]:
            st.markdown(f'<div class="info-label">{key}</div>', unsafe_allow_html=True)
            if key == "macro_segment":
                badge_class = get_badge_class(str(value))
                st.markdown(f'<div class="{badge_class}">{value}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="info-value">{value}</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


def render_table(title: str, rows, columns):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
    df = select_columns(rows, columns)
    if df.empty:
        st.info("Aucune donnée disponible.")
    else:
        st.dataframe(df, width="stretch", hide_index=True)


tab_client, tab_foyer = st.tabs(["Recherche CLIENT", "Recherche FOYER"])

# =========================
# ONGLET CLIENT
# =========================
with tab_client:
    search_mode = st.radio(
        "Mode de recherche client",
        ["ID client", "Email hash"],
        horizontal=True
    )

    if search_mode == "ID client":
        search_value = st.text_input("ID client", key="customer_id_input")
        search_params = {"customer_id": search_value} if search_value else None
    else:
        search_value = st.text_input("Email hash", key="email_hash_input")
        search_params = {"email_hash": search_value} if search_value else None

    show_customer_list = st.button(
        "Afficher la liste des clients",
        width="stretch",
        key="liste_clients"
    )

    if show_customer_list:
        try:
            data = fetch_json("/gold/customer-segmentation/list", params={"limit": 50})
            render_table(
                "Liste des clients segmentés",
                data,
                ["customer_id", "customer_segment"]
            )
            st.divider()
        except Exception as e:
            st.error(f"Erreur lors du chargement de la liste des clients : {e}")

    col_btn = st.columns([1, 2, 1])
    with col_btn[1]:
        search_customer = st.button(
            "Rechercher un client",
            type="primary",
            width="stretch",
            key="rechercher_client"
        )

    if search_customer:
        if not search_value:
            st.warning("Veuillez saisir une valeur de recherche.")
        else:
            try:
                data = fetch_json("/gold/customer-segmentation/search", params=search_params)

                customer = data.get("customer", {})
                household = data.get("household", {})
                household_segmentation = data.get("household_segmentation", {})
                foyer_data = merge_household_data(household, household_segmentation)

                st.divider()

                c1, space, c2 = st.columns([1, 0.08, 1])

                with c1:
                    render_info_card(
                        "Informations client",
                        {k: customer.get(k, "") for k in [
                            "customer_id",
                            "household_id",
                            "first_name",
                            "last_name",
                            "birth_year",
                            "email",
                            "email_hash", 
                            "customer_city",
                            "postal_code",
                            "region",
                            "nb_transactions",
                            "total_spent",
                            "avg_item_price",
                            "customer_segment",
                        ]}
                    )

                with c2:
                    render_household_card("Informations du foyer", foyer_data)

                render_table(
                    "Cartes de fidélité",
                    data.get("loyalty_cards", []),
                    ["card_id", "card_status", "issued_at", "last_used_at"]
                )

                render_table(
                    "Transactions du client",
                    data.get("transactions", []),
                    ["transaction_id", "transaction_timestamp", "transaction_amount"]
                )

            except requests.HTTPError as e:
                if e.response is not None and e.response.status_code == 404:
                    st.error("Client introuvable.")
                elif e.response is not None and e.response.status_code == 400:
                    try:
                        detail = e.response.json().get("detail", "Requête invalide.")
                    except Exception:
                        detail = "Requête invalide."
                    st.error(detail)
                else:
                    st.error(f"Erreur API : {e}")
            except Exception as e:
                st.error(f"Erreur : {e}")

# =========================
# ONGLET FOYER
# =========================
with tab_foyer:
    household_id = st.text_input("ID foyer", key="household_id_input")

    show_household_list = st.button(
        "Afficher la liste des foyers",
        width="stretch",
        key="liste_households"
    )

    if show_household_list:
        try:
            data = fetch_json("/search/households", params={"limit": 50})
            render_table(
                "Liste des foyers",
                data,
                ["household_id", "household_created_at"]
            )
            st.divider()
        except Exception as e:
            st.error(f"Erreur lors du chargement de la liste des foyers : {e}")

    col_btn = st.columns([1, 2, 1])
    with col_btn[1]:
        search_household = st.button(
            "Rechercher un foyer",
            type="primary",
            width="stretch",
            key="rechercher_household"
        )

    if search_household:
        if not household_id:
            st.warning("Veuillez saisir un ID foyer.")
        else:
            try:
                data = fetch_json(f"/search/household/{household_id}")

                household = data.get("household", {})
                household_segmentation = data.get("household_segmentation", {})
                foyer_data = merge_household_data(household, household_segmentation)

                st.divider()

                render_household_card("Informations du foyer", foyer_data)

                render_table(
                    "Clients du foyer",
                    data.get("customers", []),
                    [
                        "customer_id",
                        "first_name",
                        "last_name",
                        "email",
                        "birth_year",
                        "customer_city",
                        "postal_code",
                        "region",
                    ]
                )

                render_table(
                    "Transactions du foyer",
                    data.get("transactions", []),
                    ["transaction_id", "customer_id", "transaction_timestamp", "transaction_amount"]
                )

            except requests.HTTPError as e:
                if e.response is not None and e.response.status_code == 404:
                    st.error("Foyer introuvable.")
                else:
                    st.error(f"Erreur API : {e}")
            except Exception as e:
                st.error(f"Erreur : {e}")