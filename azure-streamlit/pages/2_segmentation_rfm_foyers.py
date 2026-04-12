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


def fetch_rfm_distributions() -> dict:
    response = requests.get(f"{API_BASE_URL}/gold/rfm/distributions", timeout=60)
    response.raise_for_status()
    return response.json()


def safe_dataframe(data):
    if isinstance(data, list):
        return pd.DataFrame(data)
    return pd.DataFrame()


def add_percentage(df: pd.DataFrame, count_col: str = "count") -> pd.DataFrame:
    if not df.empty and count_col in df.columns:
        total = df[count_col].sum()
        if total > 0:
            df["percent"] = (df[count_col] / total) * 100
        else:
            df["percent"] = 0
    return df


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
    text-align: center;
}

.helper-text {
    text-align: center;
    font-size: 15px;
    color: #666;
    font-style: italic;
    margin-bottom: 12px;
}

.insight-box {
    background-color: #f7f7f7;
    padding: 12px 14px;
    border-radius: 10px;
    border-left: 5px solid #004f9f;
    font-size: 14px;
    color: #1f2a44;
    margin-top: 8px;
}

.rfm-table-wrapper {
    margin-top: 10px;
    margin-bottom: 10px;
}

.rfm-table {
    width: 100%;
    border-collapse: collapse;
    font-family: Arial, sans-serif;
    font-size: 16px;
    background-color: white;
}

.rfm-table th,
.rfm-table td {
    border: 1px solid #333;
    padding: 10px 12px;
    text-align: center;
    vertical-align: middle;
}

.rfm-table th:first-child,
.rfm-table td:first-child {
    text-align: left;
    font-weight: 700;
    width: 30%;
}

.rfm-table th {
    background-color: #f2f2f2;
    font-size: 17px;
}

.seg-premium {
    color: #b8860b;
    font-weight: 700;
}

.seg-fort-potentiel {
    color: #7b61ff;
    font-weight: 700;
}

.seg-fideles {
    color: #2a9d8f;
    font-weight: 700;
}

.seg-standard {
    color: #004f9f;
    font-weight: 700;
}

.seg-reactiver {
    color: #f4a261;
    font-weight: 700;
}

.seg-perdus {
    color: #d62828;
    font-weight: 700;
}

.icon-cell {
    font-size: 16px;
    white-space: nowrap;
    text-align: center;
    line-height: 1.6;
}
</style>
""", unsafe_allow_html=True)

st.markdown(
    '<div class="page-title-small">Segmentation RFM</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="page-subtitle-small">Analyse des foyers selon la récence, la fréquence et le montant</div>',
    unsafe_allow_html=True
)

st.divider()

try:
    payload = fetch_rfm_distributions()

    total_households = payload.get("total_households", 0)

    df_macro = safe_dataframe(payload.get("macro_segments", []))
    df_recency = safe_dataframe(payload.get("recency_segments", []))
    df_frequency = safe_dataframe(payload.get("frequency_segments", []))
    df_monetary = safe_dataframe(payload.get("monetary_segments", []))

    st.markdown(
        f"<p class='info-text'>Nombre total de foyers segmentés : <b>{int(total_households):,}</b></p>".replace(",", " "),
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            '<div class="section-title">Analyse des foyers selon la récence</div>',
            unsafe_allow_html=True
        )

        if not df_recency.empty and {"recency_segment", "count"}.issubset(df_recency.columns):
            recency_order = ["tres actif", "actif modere", "a risque", "inactif"]
            df_recency["recency_segment"] = pd.Categorical(
                df_recency["recency_segment"],
                categories=recency_order,
                ordered=True
            )
            df_recency = df_recency.sort_values("recency_segment")
            df_recency = add_percentage(df_recency)

            bars = (
                alt.Chart(df_recency)
                .mark_bar(color="#d62828", cornerRadiusTopLeft=5, cornerRadiusTopRight=5)
                .encode(
                    x=alt.X("recency_segment:N", title="Segment"),
                    y=alt.Y("count:Q", title="Nombre de foyers"),
                    tooltip=[
                        alt.Tooltip("recency_segment:N", title="Segment"),
                        alt.Tooltip("count:Q", title="Nombre de foyers"),
                        alt.Tooltip("percent:Q", title="Part (%)", format=".1f")
                    ]
                )
                .properties(height=300)
            )

            labels = (
                alt.Chart(df_recency)
                .mark_text(align="center", baseline="bottom", dy=-5, color="black")
                .encode(
                    x="recency_segment:N",
                    y="count:Q",
                    text="count:Q"
                )
            )

            st.altair_chart((bars + labels).configure_view(strokeWidth=0), use_container_width=True)

            top_recency = df_recency.sort_values("count", ascending=False).iloc[0]
            st.markdown(
                f"<div class='insight-box'>Le segment de récence dominant est <b>{top_recency['recency_segment']}</b> avec <b>{top_recency['count']:,}</b> foyers, soit <b>{top_recency['percent']:.1f}%</b> du total.</div>".replace(",", " "),
                unsafe_allow_html=True
            )
        else:
            st.info("Aucune donnée disponible.")

    with col2:
        st.markdown(
            '<div class="section-title">Analyse des foyers selon la fréquence</div>',
            unsafe_allow_html=True
        )

        if not df_frequency.empty and {"frequency_segment", "count"}.issubset(df_frequency.columns):
            frequency_order = ["faible", "moyenne", "elevee"]
            df_frequency["frequency_segment"] = pd.Categorical(
                df_frequency["frequency_segment"],
                categories=frequency_order,
                ordered=True
            )
            df_frequency = df_frequency.sort_values("frequency_segment")
            df_frequency = add_percentage(df_frequency)

            bars = (
                alt.Chart(df_frequency)
                .mark_bar(color="#004f9f", cornerRadiusTopLeft=5, cornerRadiusTopRight=5)
                .encode(
                    x=alt.X("frequency_segment:N", title="Segment"),
                    y=alt.Y("count:Q", title="Nombre de foyers"),
                    tooltip=[
                        alt.Tooltip("frequency_segment:N", title="Segment"),
                        alt.Tooltip("count:Q", title="Nombre de foyers"),
                        alt.Tooltip("percent:Q", title="Part (%)", format=".1f")
                    ]
                )
                .properties(height=300)
            )

            labels = (
                alt.Chart(df_frequency)
                .mark_text(align="center", baseline="bottom", dy=-5, color="black")
                .encode(
                    x="frequency_segment:N",
                    y="count:Q",
                    text="count:Q"
                )
            )

            st.altair_chart((bars + labels).configure_view(strokeWidth=0), use_container_width=True)

            top_frequency = df_frequency.sort_values("count", ascending=False).iloc[0]
            st.markdown(
                f"<div class='insight-box'>Le segment de fréquence dominant est <b>{top_frequency['frequency_segment']}</b> avec <b>{top_frequency['count']:,}</b> foyers, soit <b>{top_frequency['percent']:.1f}%</b> du total.</div>".replace(",", " "),
                unsafe_allow_html=True
            )
        else:
            st.info("Aucune donnée disponible.")

    with col3:
        st.markdown(
            '<div class="section-title">Analyse des foyers selon le montant</div>',
            unsafe_allow_html=True
        )

        if not df_monetary.empty and {"monetary_segment", "count"}.issubset(df_monetary.columns):
            monetary_order = [
                "petit panier",
                "panier moyen",
                "grand panier",
                "tres grand panier"
            ]
            df_monetary["monetary_segment"] = pd.Categorical(
                df_monetary["monetary_segment"],
                categories=monetary_order,
                ordered=True
            )
            df_monetary = df_monetary.sort_values("monetary_segment")
            df_monetary = add_percentage(df_monetary)

            bars = (
                alt.Chart(df_monetary)
                .mark_bar(color="#2a9d8f", cornerRadiusTopLeft=5, cornerRadiusTopRight=5)
                .encode(
                    x=alt.X("monetary_segment:N", title="Segment"),
                    y=alt.Y("count:Q", title="Nombre de foyers"),
                    tooltip=[
                        alt.Tooltip("monetary_segment:N", title="Segment"),
                        alt.Tooltip("count:Q", title="Nombre de foyers"),
                        alt.Tooltip("percent:Q", title="Part (%)", format=".1f")
                    ]
                )
                .properties(height=300)
            )

            labels = (
                alt.Chart(df_monetary)
                .mark_text(align="center", baseline="bottom", dy=-5, color="black")
                .encode(
                    x="monetary_segment:N",
                    y="count:Q",
                    text="count:Q"
                )
            )

            st.altair_chart((bars + labels).configure_view(strokeWidth=0), use_container_width=True)

            top_monetary = df_monetary.sort_values("count", ascending=False).iloc[0]
            st.markdown(
                f"<div class='insight-box'>Le segment montant dominant est <b>{top_monetary['monetary_segment']}</b> avec <b>{top_monetary['count']:,}</b> foyers, soit <b>{top_monetary['percent']:.1f}%</b> du total.</div>".replace(",", " "),
                unsafe_allow_html=True
            )
        else:
            st.info("Aucune donnée disponible.")

    st.divider()

    st.markdown(
        '<div class="section-title">Répartition finale des segments RFM</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<div class="helper-text">Cette synthèse est le résultat combiné des segmentations de récence, fréquence et montant présentées ci-dessus.</div>',
        unsafe_allow_html=True
    )

    if not df_macro.empty and {"macro_segment", "count"}.issubset(df_macro.columns):
        macro_order = [
            "Premium",
            "Fort potentiel",
            "Fideles",
            "Standard",
            "A reactiver",
            "Perdus"
        ]

        df_macro["macro_segment"] = pd.Categorical(
            df_macro["macro_segment"],
            categories=macro_order,
            ordered=True
        )
        df_macro = df_macro.sort_values("macro_segment")
        df_macro = add_percentage(df_macro)

        pie_col1, pie_col2 = st.columns([1.1, 1])

        with pie_col1:
            pie = (
                alt.Chart(df_macro)
                .mark_arc(innerRadius=95)
                .encode(
                    theta=alt.Theta("count:Q"),
                    color=alt.Color(
                        "macro_segment:N",
                        scale=alt.Scale(
                            domain=[
                                "Premium",
                                "Fort potentiel",
                                "Fideles",
                                "Standard",
                                "A reactiver",
                                "Perdus"
                            ],
                            range=[
                                "#d4af37",  # Premium
                                "#7b61ff",  # Fort potentiel
                                "#2a9d8f",  # Fideles
                                "#004f9f",  # Standard
                                "#f4a261",  # A reactiver
                                "#d62828"   # Perdus
                            ]
                        ),
                        legend=alt.Legend(
                            title="Segment",
                            orient="right",
                            labelFontSize=14,
                            titleFontSize=16
                        )
                    ),
                    tooltip=[
                        alt.Tooltip("macro_segment:N", title="Segment"),
                        alt.Tooltip("count:Q", title="Nombre de foyers"),
                        alt.Tooltip("percent:Q", title="Part (%)", format=".1f")
                    ]
                )
                .properties(height=430)
            )

            st.altair_chart(
                pie.configure_view(strokeWidth=0),
                use_container_width=True
            )

            top_macro = df_macro.sort_values("count", ascending=False).iloc[0]
            st.markdown(
                f"<div class='insight-box'>Le macro-segment dominant est <b>{top_macro['macro_segment']}</b> avec <b>{top_macro['count']:,}</b> foyers, soit <b>{top_macro['percent']:.1f}%</b> du total.</div>".replace(",", " "),
                unsafe_allow_html=True
            )

        with pie_col2:
            with st.expander("Comprendre la segmentation RFM", expanded=True):
                st.markdown(
                    """
                    <div class="rfm-table-wrapper">
                        <table class="rfm-table">
                            <thead>
                                <tr>
                                    <th>Segmentation</th>
                                    <th>Récence</th>
                                    <th>Fréquence</th>
                                    <th>Montant</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td class="seg-premium">Premium</td>
                                    <td class="icon-cell">📅&nbsp;📅&nbsp;📅</td>
                                    <td class="icon-cell">🛒&nbsp;🛒&nbsp;🛒</td>
                                    <td class="icon-cell">€&nbsp;€&nbsp;€</td>
                                </tr>
                                <tr>
                                    <td class="seg-fort-potentiel">Fort potentiel</td>
                                    <td class="icon-cell">📅&nbsp;📅</td>
                                    <td class="icon-cell">🛒&nbsp;🛒</td>
                                    <td class="icon-cell">€&nbsp;€&nbsp;€</td>
                                </tr>
                                <tr>
                                    <td class="seg-fideles">Fideles</td>
                                    <td class="icon-cell">📅&nbsp;📅&nbsp;📅</td>
                                    <td class="icon-cell">🛒&nbsp;🛒&nbsp;🛒</td>
                                    <td class="icon-cell">€</td>
                                </tr>
                                <tr>
                                    <td class="seg-standard">Standard</td>
                                    <td class="icon-cell">📅&nbsp;📅</td>
                                    <td class="icon-cell">🛒&nbsp;🛒</td>
                                    <td class="icon-cell">€&nbsp;€</td>
                                </tr>
                                <tr>
                                    <td class="seg-reactiver">A reactiver</td>
                                    <td class="icon-cell">📅</td>
                                    <td class="icon-cell">🛒</td>
                                    <td class="icon-cell">€&nbsp;€</td>
                                </tr>
                                <tr>
                                    <td class="seg-perdus">Perdus</td>
                                    <td class="icon-cell">📅</td>
                                    <td class="icon-cell">🛒</td>
                                    <td class="icon-cell">€</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
    else:
        st.info("Aucune donnée disponible pour la répartition finale des segments RFM.")

except requests.exceptions.HTTPError as e:
    st.error(f"Erreur HTTP lors du chargement de la segmentation RFM : {e}")
except requests.exceptions.ConnectionError:
    st.error("Impossible de contacter l'API pour charger la segmentation RFM.")
except requests.exceptions.Timeout:
    st.error("Le chargement de la segmentation RFM a expiré.")
except requests.exceptions.RequestException as e:
    st.error(f"Erreur de connexion à l’API : {e}")
except Exception as e:
    st.error(f"Erreur de chargement des données : {e}")