import pandas as pd
import streamlit as st

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

DATE_CONTROLE = "16/11/2026"


# ============================================================
# 2. FONCTIONS D'AFFICHAGE
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


def tableau(lignes, colonnes):
    st.dataframe(
        pd.DataFrame(lignes, columns=colonnes),
        use_container_width=True,
        hide_index=True
    )


def source(texte):
    st.caption(f"Contrôle du {DATE_CONTROLE} — {texte}")


# ============================================================
# 3. TITRE PRINCIPAL ET SYNTHÈSE
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

with st.container(border=True):
    section_title("Synthèse des contrôles d'accès")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Tests de droits réalisés", "34")
    with c2:
        st.metric("Tests conformes", "34 / 34")
    with c3:
        st.metric("Groupes et rôles", "10", help="4 groupes MinIO + 6 rôles PostgreSQL")
    with c4:
        st.metric("Comptes individuels", "10")
    st.write(
        "Les droits sont contrôlés sur les **trois accès** demandés par la politique "
        "de gouvernance : **l'alimentation** du Data Lake, **la recherche dans l'index** "
        "(catalogue) et **la récupération** des données. Les droits sont portés par des "
        "**groupes**, jamais directement par des individus, selon le principe du "
        "**moindre privilège**. Groupes et rôles : 4 groupes MinIO et 6 rôles collectifs PostgreSQL."
    )


# ============================================================
# 4. DROITS SUR LE DATA LAKE (MINIO)
# ============================================================

with st.container(border=True):
    section_title("1. Droits sur le Data Lake (MinIO)")

    st.write("Quatre groupes MinIO, chacun associé à une politique d'accès au format S3 :")
    tableau([
        ["grp-ingestion", "svc_ingestion", "Alimentation + index", "–", "–"],
        ["grp-data-engineer", "de_soufia", "Alimentation + index + récupération",
         "Alimentation + index + récupération", "Accès (traitement)"],
        ["grp-data-analyst", "analyst_demo", "–", "Index + récupération", "Refusé (règle Deny)"],
        ["grp-auditor", "auditor_demo", "Index seul", "Index seul", "–"],
    ], ["Groupe", "Compte", "Bronze", "Silver", "Données personnelles"])

    col_gauche, col_droite = st.columns([1.2, 1], gap="medium", vertical_alignment="center")
    with col_gauche:
        tableau([
            ["Alimentation", "s3:PutObject", "Déposer des données dans le lac"],
            ["Index / recherche", "s3:ListBucket", "Lister et rechercher les objets"],
            ["Récupération", "s3:GetObject", "Lire le contenu d'un objet"],
        ], ["Type de droit", "Action S3", "Signification"])
    with col_droite:
        st.info(
            "Les fichiers classés **personnels** dans le catalogue "
            "(customers.csv, loyalty_cards.csv) sont interdits en lecture aux analystes."
        )

    with st.expander("Voir le détail des 14 tests de droits sur le Data Lake (14 / 14 conformes)"):
        tableau([
            ["Ingestion", "Alimentation", "Écriture dans Bronze", "Autorisé", "Autorisé", "OK"],
            ["Ingestion", "Alimentation", "Écriture dans Silver", "Refusé", "Refusé", "OK"],
            ["Ingestion", "Récupération", "Lecture d'un fichier Bronze", "Refusé", "Refusé", "OK"],
            ["Data Engineer", "Alimentation", "Écriture dans Silver", "Autorisé", "Autorisé", "OK"],
            ["Data Engineer", "Récupération", "Lecture d'un fichier Bronze", "Autorisé", "Autorisé", "OK"],
            ["Data Engineer", "Index", "Recherche dans Bronze", "Autorisé", "Autorisé", "OK"],
            ["Data Analyst", "Index", "Recherche dans Silver", "Autorisé", "Autorisé", "OK"],
            ["Data Analyst", "Récupération", "Lecture produits Silver", "Autorisé", "Autorisé", "OK"],
            ["Data Analyst", "Récupération", "Lecture clients (RGPD)", "Refusé", "Refusé", "OK"],
            ["Data Analyst", "Index", "Recherche dans Bronze", "Refusé", "Refusé", "OK"],
            ["Data Analyst", "Alimentation", "Écriture dans Silver", "Refusé", "Refusé", "OK"],
            ["Auditeur", "Index", "Recherche dans Bronze", "Autorisé", "Autorisé", "OK"],
            ["Auditeur", "Récupération", "Lecture d'un fichier Bronze", "Refusé", "Refusé", "OK"],
            ["Auditeur", "Alimentation", "Écriture dans Bronze", "Refusé", "Refusé", "OK"],
        ], ["Rôle", "Droit", "Test", "Attendu", "Obtenu", "Résultat"])
        source("script scripts/governance/test_minio_iam.ps1 (connexion avec les identifiants de chaque compte).")


# ============================================================
# 5. DROITS DE RECHERCHE DANS LE CATALOGUE
# ============================================================

with st.container(border=True):
    section_title("2. Droits d'accès à l'index pour la recherche de données")
    st.write(
        "Le catalogue (table **catalogue.objets**, 25 objets) applique une "
        "**sécurité par ligne** (Row Level Security) : chaque rôle ne voit que les "
        "objets qu'il est autorisé à rechercher."
    )
    tableau([
        ["Data Engineer", "Recherche dans tout le catalogue", "25 objets visibles", "OK"],
        ["Auditeur", "Recherche dans tout le catalogue", "25 objets visibles", "OK"],
        ["Data Analyst", "Recherche limitée à Silver / Gold", "13 objets visibles", "OK"],
        ["Data Analyst", "Objets Bronze invisibles", "0 objet Bronze visible", "OK"],
        ["Data Analyst", "Recherche par mot-clé « products »", "1 résultat", "OK"],
        ["Data Analyst", "Modification du catalogue interdite", "UPDATE refusé", "OK"],
        ["Marketing", "Accès au catalogue interdit", "SELECT refusé", "OK"],
    ], ["Rôle", "Test", "Détail", "Résultat"])
    source("script sql/catalogue/02_catalogue_tests.sql — 7 / 7 conformes.")


# ============================================================
# 6. DROITS SUR LA BASE POSTGRESQL
# ============================================================

col_gauche, col_droite = st.columns(2, gap="medium")

with col_gauche:
    with st.container(border=True):
        section_title("3. Rôles collectifs PostgreSQL (RBAC)")
        tableau([
            ["role_data_engineer", "Lecture et insertion Streaming"],
            ["role_data_analyst", "Lecture des vues GOLD"],
            ["role_marketing", "Lecture de la synthèse agrégée (marketing_segments_summary)"],
            ["role_auditeur", "Lecture des synthèses d'audit et du journal des purges"],
            ["role_app_api", "Lecture seule, pour l'API FastAPI"],
            ["role_rgpd", "Anonymisation des seules colonnes personnelles"],
        ], ["Rôle collectif", "Permissions"])
        st.caption("Les rôles collectifs ne peuvent pas se connecter (NOLOGIN) : ils portent uniquement les droits.")

with col_droite:
    with st.container(border=True):
        section_title("4. Comptes individuels rattachés")
        tableau([
            ["u_soufia_engineer", "role_data_engineer"],
            ["u_analyst_demo", "role_data_analyst"],
            ["u_marketing_demo", "role_marketing"],
            ["u_auditeur_demo", "role_auditeur"],
            ["svc_api", "role_app_api"],
            ["svc_rgpd", "role_rgpd"],
        ], ["Compte individuel", "Rôle collectif"])
        st.caption("Aucun droit n'est attribué directement à un compte : il hérite de son rôle collectif.")

with st.container(border=True):
    section_title("5. Vérification des permissions PostgreSQL")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Rôles testés", "4")
    with c2:
        st.metric("Tests réalisés", "13")
    with c3:
        st.metric("Tests réussis", "13 / 13")

    with st.expander("Voir le détail des 13 tests RBAC"):
        tableau([
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
            ["Auditeur", "Modification interdite", "OK"],
        ], ["Rôle", "Test de permission", "Résultat"])
        source("script sql/security/02_rbac_tests.sql.")


# ============================================================
# 7. TRAÇABILITÉ
# ============================================================

col_gauche, col_droite = st.columns(2, gap="medium")

with col_gauche:
    with st.container(border=True):
        section_title("6. Journalisation PostgreSQL")
        tableau([
            ["Connexions", "log_connections = on", "Activé"],
            ["Déconnexions", "log_disconnections = on", "Activé"],
            ["Identification des utilisateurs", "log_line_prefix (utilisateur, base, horodatage)", "Activé"],
        ], ["Contrôle", "Paramètre", "État"])
        st.caption("Paramètres définis par sql/security/03_postgresql_audit.sql.")

with col_droite:
    with st.container(border=True):
        section_title("7. Traçabilité des purges RGPD")
        tableau([
            ["16/11/2026 13:38", "svc_rgpd", "simulation", "316", "0"],
            ["16/11/2026 13:42", "svc_rgpd", "exécution", "316", "316"],
        ], ["Date", "Compte", "Mode", "Clients identifiés", "Clients anonymisés"])
        st.caption("Table rgpd.journal_purge — clients inactifs depuis plus de 24 mois.")


# ============================================================
# 8. AUDIT DES ACCÈS API FASTAPI
# ============================================================

with st.container(border=True):

    section_title("8. Audit des accès API FastAPI")

    st.write(
        "Les journaux Uvicorn enregistrent les requêtes HTTP "
        "adressées à l'API FastAPI."
    )

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
    ], columns=["Date / heure (France)", "Méthode", "Endpoint", "Statut"])

    api_logs["Horodatage"] = pd.to_datetime(api_logs["Date / heure (France)"], dayfirst=True)
    api_logs = api_logs.sort_values("Horodatage", ascending=False).drop(columns="Horodatage")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Requêtes examinées", len(api_logs))
    with col2:
        st.metric("Réponses HTTP 200", int(api_logs["Statut"].eq("200 OK").sum()))

    st.dataframe(api_logs, use_container_width=True, hide_index=True)
    st.caption("Relevé des journaux du conteneur datamarket_carrefour_api.")


# ============================================================
# 9. PROCÉDURE DE MISE À JOUR DES RÈGLES
# ============================================================

with st.container(border=True):
    section_title("9. Procédure de mise à jour des règles")
    tableau([
        ["1. Demande", "Le responsable métier exprime un besoin (nouvel utilisateur, nouvel accès)."],
        ["2. Validation", "Le Data Engineer vérifie le moindre privilège ; le référent RGPD valide tout accès à des données personnelles."],
        ["3. Modification", "Mise à jour de la politique JSON ou du script SQL, versionnés dans Git."],
        ["4. Application et contrôle", "Exécution des scripts de mise en place, puis des scripts de tests (MinIO, catalogue, PostgreSQL)."],
        ["5. Révocation et revue", "Désactivation immédiate au départ d'un collaborateur ; revue trimestrielle des membres de chaque groupe."],
    ], ["Étape", "Action"])


# ============================================================
# 10. PIED DE PAGE
# ============================================================

st.divider()

st.caption(
    f"Carrefour Data Market | Audit et sécurité C21 | Contrôle du {DATE_CONTROLE} — "
    "tests rejouables à la demande avec les scripts de gouvernance du projet"
)
