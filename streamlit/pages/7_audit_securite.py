
import streamlit as st
import pandas as pd

from utils.sidebar import sidebar


# ============================================================
# 1. CONFIGURATION DE LA PAGE
# ============================================================

st.set_page_config(
    page_title="Audit et sécurité | DataMarket Carrefour",
    layout="wide",
    initial_sidebar_state="expanded"
)

sidebar("Audit")


# ============================================================
# 2. FONCTION POUR LES SOUS-TITRES
# ============================================================

def section_title(titre):
    st.markdown(
        f"""
        <h3 style="
            text-decoration: underline;
            text-decoration-color: #0046AD;
            text-underline-offset: 6px;
            font-size: 21px;
            font-weight: 700;
            margin-bottom: 15px;
        ">
            {titre}
        </h3>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# 3. TITRE PRINCIPAL
# ============================================================

st.markdown(
    """
    <h1 style="
        text-align: center;
        color: #0046AD;
        font-size: 42px;
        font-weight: 800;
        margin-bottom: 8px;
    ">
        Audit et sécurité des données
    </h1>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <p style="
        text-align: center;
        color: #777777;
        font-size: 15px;
        margin-bottom: 25px;
    ">
        Carrefour Data Market | Compétence C21
    </p>
    """,
    unsafe_allow_html=True
)


# ============================================================
# 4. GESTION DES ACCÈS ET TESTS RBAC
# ============================================================

col_gauche, col_droite = st.columns(2, gap="medium")

# ------------------------------------------------------------
# 4.1 GESTION DES ACCÈS
# ------------------------------------------------------------

with col_gauche:
    with st.container(border=True):

        section_title("1. Gestion des accès PostgreSQL (RBAC)")

        st.write(
            "Les permissions sont attribuées selon le "
            "principe du moindre privilège."
        )

        roles = pd.DataFrame([
            {
                "Rôle": "Data Engineer",
                "Permissions": "Lecture et insertion Streaming"
            },
            {
                "Rôle": "Data Analyst",
                "Permissions": "Lecture des vues GOLD"
            },
            {
                "Rôle": "Marketing",
                "Permissions": "Lecture des vues métier"
            },
            {
                "Rôle": "Auditeur",
                "Permissions": "Lecture des synthèses d'audit"
            }
        ])

        st.dataframe(
            roles,
            use_container_width=True,
            hide_index=True
        )


# ------------------------------------------------------------
# 4.2 VÉRIFICATION DES PERMISSIONS
# ------------------------------------------------------------

with col_droite:
    with st.container(border=True):

        section_title("2. Vérification des permissions")

        c1, c2, c3 = st.columns(3)

        with c1:
            st.metric("Rôles RBAC", "4")

        with c2:
            st.metric("Tests réalisés", "13")

        with c3:
            st.metric("Tests réussis", "13 / 13")

        st.markdown(
            "Les **13 tests de permissions** ont retourné "
            "**OK** lors du dernier contrôle. "
            "Ces résultats sont **historiques**."
        )

       
        with st.expander("Voir le détail des 13 tests RBAC"):

            tests_rbac = pd.DataFrame([
                ["Data Analyst", "Lecture RFM", "OK"],
                ["Data Analyst", "Modification RFM interdite", "OK"],
                ["Data Analyst", "Schéma clients interdit", "OK"],

                ["Marketing", "Lecture synthèse autorisée", "OK"],
                ["Marketing", "Segmentation clients interdite", "OK"],
                ["Marketing", "Schéma clients interdit", "OK"],

                ["Data Engineer", "Lecture Streaming", "OK"],
                ["Data Engineer", "Insertion Streaming", "OK"],
                ["Data Engineer", "Modification interdite", "OK"],
                ["Data Engineer", "Suppression interdite", "OK"],

                ["Auditeur", "Lecture synthèse autorisée", "OK"],
                ["Auditeur", "Transactions interdites", "OK"],
                ["Auditeur", "Modification interdite", "OK"]
            ], columns=[
                "Rôle",
                "Test de permission",
                "Résultat"
            ])

            st.dataframe(
                tests_rbac,
                use_container_width=True,
                hide_index=True
            )

            st.caption(
                "Résultats du dernier contrôle réalisé avec "
                "sql/security/02_rbac_tests.sql. "
            )


          
# ============================================================
# 5. JOURNALISATION POSTGRESQL ET SYNTHÈSE
# ============================================================

col_gauche, col_droite = st.columns(2, gap="medium")

# ------------------------------------------------------------
# 5.1 JOURNALISATION POSTGRESQL
# ------------------------------------------------------------

with col_gauche:
    with st.container(border=True):

        section_title("3. Journalisation PostgreSQL")

        audit = pd.DataFrame([
            {
                "Contrôle": "Connexions",
                "Résultat": "Vérifié"
            },
            {
                "Contrôle": "Déconnexions",
                "Résultat": "Vérifié"
            },
            {
                "Contrôle": "Identification des utilisateurs",
                "Résultat": "Vérifié"
            },
            {
                "Contrôle": "Audit détaillé des requêtes SQL",
                "Résultat": "Non mis en place"
            }
        ])

        st.dataframe(
            audit,
            use_container_width=True,
            hide_index=True
        )

        st.caption(
            "Résultats issus des paramètres PostgreSQL "
            "et des journaux Docker."
        )


# ------------------------------------------------------------
# 5.2 SYNTHÈSE DE SÉCURITÉ
# ------------------------------------------------------------

with col_droite:
    with st.container(border=True):

        section_title("4. Synthèse de sécurité")

        st.write(
            "La plateforme applique une gestion des "
            "droits par rôles RBAC et protège les "
            "données personnelles par chiffrement."
        )

        st.write(
            "Les connexions PostgreSQL sont journalisées "
            "et les requêtes API FastAPI sont tracées "
            "dans les journaux Uvicorn."
        )

      

# ============================================================
# 6. AUDIT DES ACCÈS API FASTAPI
# ============================================================

with st.container(border=True):

    section_title("5. Audit des accès API FastAPI")

    st.write(
        "Les journaux Uvicorn enregistrent les requêtes HTTP "
        "adressées à l'API FastAPI."
    )

    # Relevé historique des journaux Docker
    api_logs = pd.DataFrame([
        ["15/11/2026 14:06:06", "GET", "/gold/kpis", "200 OK"],
        ["15/11/2026 14:06:07", "GET", "/gold/revenue_over_time", "200 OK"],
        ["15/11/2026 14:06:11", "GET", "/gold/rfm/distributions", "200 OK"],
        ["15/11/2026 14:13:25", "GET", "/gold/rfm/distributions", "200 OK"],
        ["15/11/2026 14:22:32", "GET", "/gold/kpis", "200 OK"],
        ["15/11/2026 14:22:32", "GET", "/gold/revenue_over_time", "200 OK"],
        ["15/11/2026 14:30:05", "GET", "/gold/kpis", "200 OK"],
        ["15/11/2026 14:30:05", "GET", "/gold/revenue_over_time", "200 OK"],
        ["15/11/2026 14:30:09", "GET", "/gold/rfm/distributions", "200 OK"],
        ["15/11/2026 14:40:20", "GET", "/gold/rfm/distributions", "200 OK"]
    ], columns=[
        "Date / heure (France)",
        "Méthode",
        "Endpoint",
        "Statut"
    ])

    # Trier par date décroissante
    api_logs["Horodatage"] = pd.to_datetime(
        api_logs["Date / heure (France)"],
        dayfirst=True
    )

    api_logs = (
        api_logs.sort_values(
            "Horodatage",
            ascending=False
        )
        .drop(columns="Horodatage")
    )

    # Indicateurs
    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Requêtes examinées",
            len(api_logs)
        )

    with col2:
        st.metric(
            "Réponses HTTP 200",
            int(api_logs["Statut"].eq("200 OK").sum())
        )

    # Tableau des accès
    st.dataframe(
        api_logs,
        use_container_width=True,
        hide_index=True
    )

   

# ============================================================
# 7. PIED DE PAGE
# ============================================================

st.divider()

st.caption(
    "Carrefour Data Market | Audit et sécurité C21 | "
    "Résultats issus de contrôles ponctuels"
)
