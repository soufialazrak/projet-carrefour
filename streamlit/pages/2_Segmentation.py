import os
import requests
import pandas as pd
import altair as alt
import streamlit as st
from utils.sidebar import sidebar

st.set_page_config(
    page_title="Segmentation RFM",
    layout="wide"
)

sidebar("RFM")

API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000")

# =========================
# STYLE
# =========================
st.markdown("""
<style>

.page-title-small {
    text-align: center;
    color: #004f9f;
    font-size: 52px;
    font-weight: 800;
    margin-top: 0px;
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

.info-text {
    font-size: 17px;
    margin-bottom: 12px;
}

.helper-text {
    text-align: center;
    font-size: 15px;
    color: #666;
    font-style: italic;
    margin-bottom: 12px;
}

.vertical-divider {
    border-left: 2px solid #e5e5e5;
    height: 980px;
    margin-left: auto;
    margin-right: auto;
}

</style>
""", unsafe_allow_html=True)

# =========================
# TITRE
# =========================
st.markdown(
    '<div class="page-title-small">Segmentation RFM</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="page-subtitle-small">Analyse des foyers selon la récence, la fréquence et le montant</div>',
    unsafe_allow_html=True
)

st.divider()


def fetch_dataframe(endpoint: str) -> pd.DataFrame:
    url = f"{API_BASE_URL}{endpoint}"
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    return pd.DataFrame(response.json())


try:
    df_macro = fetch_dataframe("/gold/rfm/macro-segment-count")
    df_recency = fetch_dataframe("/gold/rfm/recency-segment-count")
    df_frequency = fetch_dataframe("/gold/rfm/frequency-segment-count")
    df_monetary = fetch_dataframe("/gold/rfm/monetary-segment-count")

    total_foyers = int(df_macro["count"].sum()) if not df_macro.empty else 0

    st.markdown(
        f"<p class='info-text'>Nombre total de foyers segmentés : <b>{total_foyers}</b></p>",
        unsafe_allow_html=True
    )

    left_col, divider_col, right_col = st.columns([1.3, 0.05, 1])

    with divider_col:
        st.markdown('<div class="vertical-divider"></div>', unsafe_allow_html=True)

    with left_col:
        # =========================
        # RECENCE
        # =========================
        st.markdown(
            '<div class="section-title">Analyse des foyers selon la récence</div>',
            unsafe_allow_html=True
        )

        if not df_recency.empty:
            recency_order = ["actif", "recent", "inactif"]
            df_recency["recency_segment"] = pd.Categorical(
                df_recency["recency_segment"],
                categories=recency_order,
                ordered=True
            )
            df_recency = df_recency.sort_values("recency_segment")

            bars = (
                alt.Chart(df_recency)
                .mark_bar(
                    color="#d62828",
                    cornerRadiusTopLeft=5,
                    cornerRadiusTopRight=5
                )
                .encode(
                    x=alt.X("recency_segment:N", title="Segment"),
                    y=alt.Y("count:Q", title="Nombre de foyers"),
                    tooltip=[
                        alt.Tooltip("recency_segment:N", title="Segment"),
                        alt.Tooltip("count:Q", title="Nombre de foyers")
                    ]
                )
                .properties(height=250)
            )

            labels = (
                alt.Chart(df_recency)
                .mark_text(
                    align="center",
                    baseline="bottom",
                    dy=-5,
                    color="black"
                )
                .encode(
                    x="recency_segment:N",
                    y="count:Q",
                    text="count:Q"
                )
            )

            recency_chart = (bars + labels).configure_view(strokeWidth=0)
            st.altair_chart(recency_chart, use_container_width=True)
        else:
            st.info("Aucune donnée disponible.")

        st.divider()

        # =========================
        # FREQUENCE
        # =========================
        st.markdown(
            '<div class="section-title">Analyse des foyers selon la fréquence</div>',
            unsafe_allow_html=True
        )

        if not df_frequency.empty:
            frequency_order = ["faible", "moyen", "eleve", "tres frequent"]
            df_frequency["frequency_segment"] = pd.Categorical(
                df_frequency["frequency_segment"],
                categories=frequency_order,
                ordered=True
            )
            df_frequency = df_frequency.sort_values("frequency_segment")

            bars = (
                alt.Chart(df_frequency)
                .mark_bar(
                    color="#004f9f",
                    cornerRadiusTopLeft=5,
                    cornerRadiusTopRight=5
                )
                .encode(
                    x=alt.X("frequency_segment:N", title="Segment"),
                    y=alt.Y("count:Q", title="Nombre de foyers"),
                    tooltip=[
                        alt.Tooltip("frequency_segment:N", title="Segment"),
                        alt.Tooltip("count:Q", title="Nombre de foyers")
                    ]
                )
                .properties(height=250)
            )

            labels = (
                alt.Chart(df_frequency)
                .mark_text(
                    align="center",
                    baseline="bottom",
                    dy=-5,
                    color="black"
                )
                .encode(
                    x="frequency_segment:N",
                    y="count:Q",
                    text="count:Q"
                )
            )

            frequency_chart = (bars + labels).configure_view(strokeWidth=0)
            st.altair_chart(frequency_chart, use_container_width=True)
        else:
            st.info("Aucune donnée disponible.")

        st.divider()

        # =========================
        # MONTANT
        # =========================
        st.markdown(
            '<div class="section-title">Analyse des foyers selon le montant</div>',
            unsafe_allow_html=True
        )

        if not df_monetary.empty:
            monetary_order = [
                "tres petit panier",
                "petit panier",
                "gros panier",
                "tres grand panier"
            ]
            df_monetary["monetary_segment"] = pd.Categorical(
                df_monetary["monetary_segment"],
                categories=monetary_order,
                ordered=True
            )
            df_monetary = df_monetary.sort_values("monetary_segment")

            bars = (
                alt.Chart(df_monetary)
                .mark_bar(
                    color="#2a9d8f",
                    cornerRadiusTopLeft=5,
                    cornerRadiusTopRight=5
                )
                .encode(
                    x=alt.X("monetary_segment:N", title="Segment"),
                    y=alt.Y("count:Q", title="Nombre de foyers"),
                    tooltip=[
                        alt.Tooltip("monetary_segment:N", title="Segment"),
                        alt.Tooltip("count:Q", title="Nombre de foyers")
                    ]
                )
                .properties(height=250)
            )

            labels = (
                alt.Chart(df_monetary)
                .mark_text(
                    align="center",
                    baseline="bottom",
                    dy=-5,
                    color="black"
                )
                .encode(
                    x="monetary_segment:N",
                    y="count:Q",
                    text="count:Q"
                )
            )

            monetary_chart = (bars + labels).configure_view(strokeWidth=0)
            st.altair_chart(monetary_chart, use_container_width=True)
        else:
            st.info("Aucune donnée disponible.")

    with right_col:
        st.markdown(
            '<div class="section-title">Répartition finale des segments RFM</div>',
            unsafe_allow_html=True
        )
        st.markdown(
            '<div class="helper-text">Cette synthèse reflète la combinaison des segmentations de récence, fréquence et montant.</div>',
            unsafe_allow_html=True
        )

        if not df_macro.empty:
            macro_order = ["Or", "Argent", "Bronze", "A analyser"]
            df_macro["macro_segment"] = pd.Categorical(
                df_macro["macro_segment"],
                categories=macro_order,
                ordered=True
            )
            df_macro = df_macro.sort_values("macro_segment")

            pie = (
                alt.Chart(df_macro)
                .mark_arc(innerRadius=80)
                .encode(
                    theta=alt.Theta("count:Q"),
                    color=alt.Color(
                        "macro_segment:N",
                        scale=alt.Scale(
                            domain=["Or", "Argent", "Bronze", "A analyser"],
                            range=["#d4af37", "#c0c0c0", "#cd7f32", "#6c757d"]
                        ),
                        legend=alt.Legend(title="Segment")
                    ),
                    tooltip=[
                        alt.Tooltip("macro_segment:N", title="Segment"),
                        alt.Tooltip("count:Q", title="Nombre de foyers")
                    ]
                )
                .properties(height=420)
            )

            label_text = (
                alt.Chart(df_macro)
                .mark_text(radius=155, size=14)
                .encode(
                    theta=alt.Theta("count:Q"),
                    text=alt.Text("macro_segment:N")
                )
            )

            macro_chart = (pie + label_text).configure_view(strokeWidth=0)
            st.altair_chart(macro_chart, use_container_width=True)
        else:
            st.info("Aucune donnée disponible.")

except requests.RequestException as e:
    st.error(f"Erreur de connexion à l’API : {e}")
except Exception as e:
    st.error(f"Erreur de chargement des données : {e}")