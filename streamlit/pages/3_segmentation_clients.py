import os
import requests
import pandas as pd
import altair as alt
import streamlit as st
from utils.sidebar import sidebar

st.set_page_config(
    page_title="Segmentation clients",
    layout="wide"
)

sidebar("Clients")

API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000")


def fetch_customer_segmentation_distributions() -> dict:
    response = requests.get(
        f"{API_BASE_URL}/gold/customer-segmentation/distributions",
        timeout=60
    )
    response.raise_for_status()
    return response.json()


def fetch_customer_segmentation_by_region() -> list:
    response = requests.get(
        f"{API_BASE_URL}/gold/customer-segmentation/by-region",
        timeout=60
    )
    response.raise_for_status()
    return response.json()


def safe_dataframe(data):
    if isinstance(data, list):
        return pd.DataFrame(data)
    return pd.DataFrame()


def build_html_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "<p style='text-align:center;'>Aucune donnée disponible.</p>"

    headers = "".join(f"<th>{col}</th>" for col in df.columns)

    rows_html = ""
    for _, row in df.iterrows():
        cells = []
        for i, value in enumerate(row):
            if i == 0:
                cells.append(f"<td class='region-cell'>{value}</td>")
            else:
                col_name = df.columns[i]
                if col_name == "Occasional":
                    td_class = "value-cell occasional-cell"
                elif col_name == "Regular":
                    td_class = "value-cell regular-cell"
                elif col_name == "VIP":
                    td_class = "value-cell vip-cell"
                else:
                    td_class = "value-cell"
                cells.append(f"<td class='{td_class}'>{value}</td>")
        rows_html += f"<tr>{''.join(cells)}</tr>"

    return f"""
    <div class="custom-table-wrapper">
        <table class="custom-table">
            <thead>
                <tr>{headers}</tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
    </div>
    """


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
    margin-bottom: 10px;
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

.custom-table-wrapper {
    margin-top: 15px;
    margin-bottom: 25px;
    overflow-x: auto;
    display: flex;
    justify-content: center;
}

.custom-table {
    width: 92%;
    border-collapse: collapse;
    font-family: Arial, sans-serif;
    font-size: 16px;
    background-color: white;
}

.custom-table th,
.custom-table td {
    border: 1px solid #2f2f2f;
    padding: 12px 10px;
    vertical-align: middle;
    text-align: center;
}

.custom-table th {
    background-color: #f3f3f3;
    color: #1f2a44;
    font-size: 17px;
    font-weight: 700;
}

.custom-table .region-cell {
    font-weight: 600;
    width: 28%;
    text-align: left;
    white-space: normal;
    word-break: break-word;
    background-color: #fafafa;
}

.custom-table .value-cell {
    width: 18%;
    font-weight: 700;
}

.custom-table .occasional-cell {
    background-color: #fde2e4;
    color: #9d0208;
}

.custom-table .regular-cell {
    background-color: #e8f1ff;
    color: #004f9f;
}

.custom-table .vip-cell {
    background-color: #fff4cc;
    color: #9a6700;
}

</style>
""", unsafe_allow_html=True)

# =========================
# TITRE
# =========================
st.markdown(
    '<div class="page-title-small">Segmentation clients</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="page-subtitle-small">Analyse de la segmentation clients globale et par région</div>',
    unsafe_allow_html=True
)

st.divider()

try:
    distributions_payload = fetch_customer_segmentation_distributions()
    regions_payload = fetch_customer_segmentation_by_region()

    total_clients = distributions_payload.get("total_clients", 0)

    df_segments = safe_dataframe(
        distributions_payload.get("segments")
        or distributions_payload.get("distribution")
        or distributions_payload.get("customer_segments")
        or []
    )

    df_regions = safe_dataframe(regions_payload)

    st.markdown(
        f"<p class='info-text'>Nombre total de clients segmentés : <b>{int(total_clients):,}</b></p>".replace(",", " "),
        unsafe_allow_html=True
    )

    possible_segment_cols_global = ["segment", "Segment", "customer_segment", "label"]
    possible_count_cols_global = ["count", "Count", "total", "nb_clients"]

    segment_col_global = next((c for c in possible_segment_cols_global if c in df_segments.columns), None)
    count_col_global = next((c for c in possible_count_cols_global if c in df_segments.columns), None)

    possible_region_cols = ["region", "Region", "customer_region", "region_name"]
    possible_segment_cols_region = ["segment", "Segment", "customer_segment"]
    possible_count_cols_region = ["count", "Count", "total"]

    region_col = next((c for c in possible_region_cols if c in df_regions.columns), None)
    segment_col_region = next((c for c in possible_segment_cols_region if c in df_regions.columns), None)
    count_col_region = next((c for c in possible_count_cols_region if c in df_regions.columns), None)

    # =========================
    # DEUX GRAPHES SUR LA MEME LIGNE
    # =========================
    st.markdown(
        '<div class="section-title">Analyse des segments clients</div>',
        unsafe_allow_html=True
    )

    col1, col2 = st.columns([1, 1.4])

    with col1:
        st.markdown(
            "<p style='text-align:center; font-weight:700;'>Répartition globale</p>",
            unsafe_allow_html=True
        )

        if not df_segments.empty and segment_col_global and count_col_global:
            chart = (
                alt.Chart(df_segments)
                .mark_bar(color="#d62828", cornerRadiusTopLeft=5, cornerRadiusTopRight=5)
                .encode(
                    x=alt.X(f"{segment_col_global}:N", title="Segment", sort="-y"),
                    y=alt.Y(f"{count_col_global}:Q", title="Nombre de clients"),
                    tooltip=[
                        alt.Tooltip(f"{segment_col_global}:N", title="Segment"),
                        alt.Tooltip(f"{count_col_global}:Q", title="Nombre")
                    ]
                )
                .properties(height=300)
            )

            labels = (
                alt.Chart(df_segments)
                .mark_text(align="center", baseline="bottom", dy=-5)
                .encode(
                    x=alt.X(f"{segment_col_global}:N", sort="-y"),
                    y=f"{count_col_global}:Q",
                    text=f"{count_col_global}:Q"
                )
            )

            st.altair_chart((chart + labels).configure_view(strokeWidth=0), width="stretch")
        else:
            st.info("Pas de données globales")

    with col2:
        st.markdown(
            "<p style='text-align:center; font-weight:700;'>Par région</p>",
            unsafe_allow_html=True
        )

        if not df_regions.empty and region_col and segment_col_region and count_col_region:
            heatmap = (
                alt.Chart(df_regions)
                .mark_rect()
                .encode(
                    x=alt.X(f"{region_col}:N", title="Région"),
                    y=alt.Y(f"{segment_col_region}:N", title="Segment"),
                    color=alt.Color(f"{count_col_region}:Q", title="Nb clients"),
                    tooltip=[
                        alt.Tooltip(f"{region_col}:N", title="Région"),
                        alt.Tooltip(f"{segment_col_region}:N", title="Segment"),
                        alt.Tooltip(f"{count_col_region}:Q", title="Nb")
                    ]
                )
                .properties(height=300)
            )

            st.altair_chart(heatmap.configure_view(strokeWidth=0), width="stretch")
        else:
            st.info("Pas de données région")

    st.divider()

    # =========================
    # TABLEAU STYLÉ
    # =========================
    st.markdown(
        '<div class="section-title">Tableau récapitulatif par région</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="helper-text">Synthèse des segments Occasional, Regular et VIP par région.</div>',
        unsafe_allow_html=True
    )

    if not df_regions.empty and region_col and segment_col_region and count_col_region:
        pivot_df = (
            df_regions
            .pivot(index=region_col, columns=segment_col_region, values=count_col_region)
            .fillna(0)
            .astype(int)
            .reset_index()
        )

        pivot_df = pivot_df.rename(columns={region_col: "Région"})

        desired_columns = ["Région", "Occasional", "Regular", "VIP"]
        existing_columns = [col for col in desired_columns if col in pivot_df.columns]
        other_columns = [col for col in pivot_df.columns if col not in existing_columns]
        pivot_df = pivot_df[existing_columns + other_columns]

        st.markdown(build_html_table(pivot_df), unsafe_allow_html=True)
    else:
        st.info("Colonnes attendues introuvables pour construire le tableau par région.")

except requests.exceptions.HTTPError as e:
    st.error(f"Erreur HTTP lors du chargement de la segmentation clients : {e}")
except requests.exceptions.ConnectionError:
    st.error("Impossible de contacter l'API pour charger la segmentation clients.")
except requests.exceptions.Timeout:
    st.error("Le chargement de la segmentation clients a expiré.")
except requests.exceptions.RequestException as e:
    st.error(f"Erreur de connexion à l’API : {e}")
except Exception as e:
    st.error(f"Erreur de chargement des données : {e}")