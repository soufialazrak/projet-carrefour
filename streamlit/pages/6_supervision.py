from __future__ import annotations

import base64
import json
import mimetypes
import os
from datetime import datetime
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
# Dossier logs/ du projet, monte en lecture seule dans le conteneur Streamlit
LOG_DIR = Path(os.environ.get("MONITORING_LOG_DIR", "/monitoring_logs"))

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


# ============================================================
# Lecture des resultats produits par scripts/monitoring/check_datalake.py
# ============================================================
def lire_json(nom: str) -> dict | None:
    chemin = LOG_DIR / nom
    try:
        return json.loads(chemin.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def heure_locale(iso: str | None) -> str:
    """Affiche une date ISO a l'heure de Paris (le conteneur Airflow est en UTC)."""
    if not iso:
        return "inconnue"
    try:
        moment = datetime.fromisoformat(iso)
        try:
            from zoneinfo import ZoneInfo
            moment = moment.astimezone(ZoneInfo("Europe/Paris"))
        except Exception:
            pass
        return moment.strftime("%d/%m/%Y à %H:%M")
    except ValueError:
        return iso


def lire_alertes(nb: int = 10) -> pd.DataFrame:
    chemin = LOG_DIR / "alertes_monitoring.log"
    lignes = []
    try:
        for ligne in chemin.read_text(encoding="utf-8").splitlines():
            # format : 2026-11-16 13:57:11 [CRITIQUE] MinIO - message
            try:
                horodatage, reste = ligne[:19], ligne[20:]
                niveau, reste = reste[1:].split("] ", 1)
                composant, message = reste.split(" - ", 1)
                lignes.append({"Date": horodatage, "Niveau": niveau,
                               "Composant": composant, "Message": message})
            except ValueError:
                continue
    except OSError:
        pass
    return pd.DataFrame(lignes[-nb:][::-1], columns=["Date", "Niveau", "Composant", "Message"])


def format_nombre(valeur: float) -> str:
    return f"{int(valeur):,}".replace(",", " ")


# ============================================================
# Composants graphiques
# ============================================================
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
        st.markdown(f'<div class="section-title">{escape(name)}</div>', unsafe_allow_html=True)
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


# ============================================================
# En-tete et etat global
# ============================================================
st.markdown('<div class="page-title-small">Supervision du Data Lake</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="page-subtitle-small">Carrefour Data Market | Compétence C20</div>',
    unsafe_allow_html=True,
)

controle = lire_json("monitoring_dernier_controle.json")
docker = lire_json("monitoring_docker.json")

if controle is None:
    st.warning(
        "Aucun résultat de supervision disponible. Lancez "
        "`python scripts/monitoring/check_datalake.py` ou activez le DAG "
        "`carrefour_monitoring_e7` dans Airflow."
    )
    st.stop()

mesures = controle.get("mesures", {})
alertes_en_cours = controle.get("alertes", [])

info_col, bouton_col = st.columns([5, 1], vertical_alignment="center")
with info_col:
    st.markdown(
        f"Dernier contrôle : <b>{heure_locale(controle.get('horodatage_iso'))}</b> "
        f"(lancé depuis : {escape(controle.get('origine', 'inconnu'))}) — "
        f"contrôle automatique toutes les 10 minutes par Airflow.",
        unsafe_allow_html=True,
    )
with bouton_col:
    if st.button("Actualiser", use_container_width=True):
        st.rerun()

if alertes_en_cours:
    texte = "<br>".join(
        f"<b>[{escape(a['niveau'])}] {escape(a['composant'])}</b> : {escape(a['message'])}"
        for a in alertes_en_cours
    )
    st.markdown(
        f'<div style="background:#fdecea;border-left:6px solid #d62828;padding:12px 16px;'
        f'border-radius:10px;color:#7a1010;margin:10px 0;">'
        f'<b>{len(alertes_en_cours)} alerte(s) en cours</b><br>{texte}</div>',
        unsafe_allow_html=True,
    )
else:
    st.success("Aucune alerte : tous les services contrôlés sont opérationnels.")


# ============================================================
# 1. DOCKER — derniere mesure des conteneurs (poste hote)
# ============================================================
with st.container(border=True):
    component_header("Docker", "docker.png", "Ressources et état des conteneurs")
    st.divider()

    if docker and docker.get("conteneurs"):
        details = pd.DataFrame(docker["conteneurs"]).rename(columns={
            "conteneur": "Conteneur", "etat": "État", "cpu_pct": "CPU (%)",
            "ram_mio": "RAM (Mio)", "ram_pct": "RAM (%)", "statut": "Statut",
        })
        ram_totale = details["RAM (Mio)"].fillna(0).sum() / 1024
        actifs = int((details["État"] == "running").sum())

        docker_kpi, docker_table = st.columns([1, 2], gap="large", vertical_alignment="center")
        with docker_kpi:
            kpi_circle("Mémoire observée", f"{ram_totale:.2f} Gio".replace(".", ","))
            st.markdown(
                f"<div style='text-align:center;'>Conteneurs actifs : "
                f"<b>{actifs} / {len(details)}</b></div>",
                unsafe_allow_html=True,
            )
        with docker_table:
            st.markdown('<div class="table-heading">Détail des conteneurs</div>', unsafe_allow_html=True)
            st.dataframe(
                details[["Conteneur", "État", "CPU (%)", "RAM (Mio)", "RAM (%)", "Statut"]],
                use_container_width=True, hide_index=True,
                column_config={
                    "CPU (%)": st.column_config.NumberColumn(format="%.2f"),
                    "RAM (Mio)": st.column_config.NumberColumn(format="%.1f"),
                    "RAM (%)": st.column_config.NumberColumn(format="%.1f"),
                },
            )
        insight_box(
            f"Mesure des conteneurs du <b>{heure_locale(docker.get('horodatage_iso'))}</b>, "
            "réalisée depuis le poste hôte (<code>docker stats</code>). "
            "Seuils d'alerte : conteneur arrêté, mémoire &gt; 80 %, CPU &gt; 90 %."
        )
    else:
        insight_box(
            "Aucune mesure des conteneurs disponible : lancez "
            "<code>python scripts/monitoring/check_datalake.py</code> depuis le poste hôte."
        )


# ============================================================
# 2. MINIO — disponibilite et espace occupe
# ============================================================
minio = mesures.get("minio", {})
with st.container(border=True):
    minio_infos, minio_graph = st.columns([1, 1.2], gap="large", vertical_alignment="top")

    with minio_infos:
        component_header("MinIO", "minio.png", "Stockage objet du Data Lake")
        st.divider()
        buckets = minio.get("buckets", {})
        volume_total = sum(b["volume_mo"] for b in buckets.values())
        objets_total = sum(b["objets"] for b in buckets.values())
        volume_col, http_col = st.columns(2)
        with volume_col:
            st.metric("Espace occupé", f"{volume_total:.1f} Mio".replace(".", ","),
                      help=f"{objets_total} objets")
        with http_col:
            st.metric("Code HTTP", str(minio.get("http")) if minio.get("disponible") else "Aucune réponse")
        if minio.get("disponible"):
            insight_box(
                f"MinIO a répondu <b>HTTP {minio.get('http')}</b> au point de santé "
                f"<b>/minio/health/live</b>. {objets_total} objets répartis dans "
                f"{len(buckets)} buckets. Seuil d'alerte : 5 Go par bucket."
            )
        else:
            insight_box("<b style='color:#d62828;'>MinIO ne répond pas : rupture de service du stockage.</b>")

    with minio_graph:
        st.markdown('<div class="chart-title">Répartition du stockage MinIO</div>', unsafe_allow_html=True)
        if buckets:
            stockage = pd.DataFrame(
                [{"Zone": nom.replace("phenix-", "").capitalize(), "Volume (Mio)": b["volume_mo"]}
                 for nom, b in buckets.items()]
            )
            stockage["Pourcentage"] = stockage["Volume (Mio)"] / stockage["Volume (Mio)"].sum() * 100
            stockage["Étiquette"] = stockage["Pourcentage"].map(lambda v: f"{v:.1f} %".replace(".", ","))
            secteurs = alt.Chart(stockage).mark_arc().encode(
                theta=alt.Theta("Volume (Mio):Q", stack=True),
                color=alt.Color(
                    "Zone:N",
                    scale=alt.Scale(domain=["Bronze", "Silver", "Gold"],
                                    range=["#C47A36", "#A0A8B5", "#D4A017"]),
                    legend=alt.Legend(title="Couche", orient="right"),
                ),
                order=alt.Order("Zone:N", sort="ascending"),
                tooltip=[alt.Tooltip("Zone:N", title="Couche"),
                         alt.Tooltip("Volume (Mio):Q", title="Volume (Mio)"),
                         alt.Tooltip("Pourcentage:Q", title="Part (%)", format=".1f")],
            )
            pourcentages = alt.Chart(stockage).mark_text(
                radius=85, fontSize=16, fontWeight="bold", color="white"
            ).encode(
                theta=alt.Theta("Volume (Mio):Q", stack=True),
                order=alt.Order("Zone:N", sort="ascending"),
                text=alt.Text("Étiquette:N"),
            )
            st.altair_chart((secteurs + pourcentages).properties(height=310).configure_view(strokeWidth=0),
                            use_container_width=True)
            st.caption(" | ".join(f"{r['Zone']} : {r['Volume (Mio)']:.1f} Mio ({r['Étiquette']})"
                                  for _, r in stockage.iterrows()))
        else:
            st.info("Volumes indisponibles (MinIO ne répond pas).")


# ============================================================
# 3. POSTGRESQL — disponibilite et volumes des tables
# ============================================================
postgres = mesures.get("postgresql", {})
with st.container(border=True):
    component_header("PostgreSQL", "postgresql.jpg", "Volumes des tables du Data Market")
    st.divider()
    if postgres.get("disponible") and postgres.get("tables"):
        tables = pd.DataFrame(list(postgres["tables"].items()), columns=["Table", "Enregistrements"])
        pg_kpi, pg_table = st.columns([1, 2], gap="large", vertical_alignment="center")
        with pg_kpi:
            kpi_circle("Total des enregistrements", format_nombre(tables["Enregistrements"].sum()))
            st.markdown(
                f"<div style='text-align:center;'>Taille de la base : <b>{escape(str(postgres.get('taille_base')))}</b></div>",
                unsafe_allow_html=True,
            )
        with pg_table:
            st.markdown('<div class="table-heading">Détail des tables PostgreSQL</div>', unsafe_allow_html=True)
            st.dataframe(tables, use_container_width=True, hide_index=True,
                         column_config={"Enregistrements": st.column_config.NumberColumn(format="%d")})
    else:
        insight_box("<b style='color:#d62828;'>PostgreSQL injoignable : rupture de service.</b>")


# ============================================================
# 4 et 5. AIRFLOW / REDPANDA
# ============================================================
airflow_col, redpanda_col = st.columns(2, gap="medium")

with airflow_col:
    with st.container(border=True):
        component_header("Apache Airflow", "airflow.png", "Orchestration et automatisation")
        st.divider()
        st.dataframe(
            pd.DataFrame({
                "DAG": ["carrefour_streaming_e7", "carrefour_monitoring_e7", "carrefour_rgpd_e7"],
                "Rôle": ["Pipeline Streaming", "Supervision et alertes", "Procédure RGPD"],
                "Planification": ["Toutes les heures", "Toutes les 10 minutes", "Le 1er du mois"],
            }),
            use_container_width=True, hide_index=True,
        )
        insight_box("Suivi détaillé des exécutions dans l'interface Airflow (<b>localhost:8080</b>).")

with redpanda_col:
    with st.container(border=True):
        component_header("Redpanda", "redpanda.png", "Streaming compatible Kafka")
        st.divider()
        redpanda = mesures.get("redpanda", {})
        st.markdown("Topic : `phenix.transactions.e7`")
        if redpanda.get("disponible"):
            insight_box(f"Broker <b>{escape(redpanda.get('broker', ''))}</b> : <b>joignable</b>.")
        else:
            insight_box(
                f"<b style='color:#d62828;'>Broker {escape(redpanda.get('broker', ''))} injoignable : "
                f"flux temps réel interrompu.</b>"
            )


# ============================================================
# 6. HISTORIQUE DES ALERTES
# ============================================================
with st.container(border=True):
    st.markdown('<div class="section-title">Historique des alertes</div>', unsafe_allow_html=True)
    historique = lire_alertes()
    if historique.empty:
        insight_box("Aucune alerte enregistrée.")
    else:
        st.dataframe(historique, use_container_width=True, hide_index=True)
        st.caption("Les 10 dernières alertes (fichier logs/alertes_monitoring.log, "
                   "également historisées dans la table PostgreSQL monitoring.alertes).")
