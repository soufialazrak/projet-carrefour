
from datetime import datetime, timedelta
from pathlib import Path
import json
import os
import subprocess
import sys

import psycopg2
from minio import Minio

from airflow import DAG
from airflow.operators.python import PythonOperator


# ============================================================
# CARREFOUR DATAMARKET - E7
# Orchestration du pipeline Kafka / MinIO / PostgreSQL
# ============================================================

SCRIPTS_DIR = "/opt/airflow/project/scripts/e7_streaming"

BRONZE_BUCKET = "phenix-bronze"
SILVER_BUCKET = "phenix-silver"
STREAMING_PREFIX = "streaming/transactions/"


def get_minio_client():
    """Connexion MinIO avec les variables Docker."""
    return Minio(
        os.environ["MINIO_ENDPOINT"],
        access_key=os.environ["MINIO_ROOT_USER"],
        secret_key=os.environ["MINIO_ROOT_PASSWORD"],
        secure=False,
    )


def lister_objets(client, bucket):
    """Liste les fichiers JSON du pipeline streaming."""
    return sorted(
        obj.object_name
        for obj in client.list_objects(
            bucket,
            prefix=STREAMING_PREFIX,
            recursive=True,
        )
        if obj.object_name.endswith(".json")
    )


# ============================================================
# TACHE 1 - VERIFIER LES SOURCES
# ============================================================

def verifier_sources():
    """Verifie la disponibilite des buckets et des evenements."""
    client = get_minio_client()

    for bucket in (BRONZE_BUCKET, SILVER_BUCKET):
        if not client.bucket_exists(bucket):
            raise RuntimeError(f"Bucket introuvable : {bucket}")

    objets_bronze = lister_objets(client, BRONZE_BUCKET)

    if not objets_bronze:
        raise RuntimeError(
            "Aucun evenement streaming disponible dans Bronze."
        )

    print(f"OK - Bronze : {len(objets_bronze)} fichiers JSON")
    print("OK - Buckets Bronze et Silver accessibles")


# ============================================================
# TACHE 2 - EXECUTER BRONZE VERS SILVER
# ============================================================

def executer_script(nom_script):
    """Execute un script Python et remonte les erreurs a Airflow."""
    chemin = Path(SCRIPTS_DIR) / nom_script

    if not chemin.is_file():
        raise FileNotFoundError(f"Script introuvable : {chemin}")

    subprocess.run(
        [sys.executable, str(chemin)],
        check=True,
        timeout=600,
    )


# ============================================================
# TACHE 3 - CONTROLER LA QUALITE SILVER
# ============================================================

def controler_qualite_silver():
    """Controle la structure des evenements Silver."""
    client = get_minio_client()
    objets = lister_objets(client, SILVER_BUCKET)

    if not objets:
        raise RuntimeError("Aucun evenement dans Silver.")

    identifiants = set()
    erreurs = []

    for nom_objet in objets:
        reponse = client.get_object(SILVER_BUCKET, nom_objet)

        try:
            evenement = json.loads(reponse.read())
        finally:
            reponse.close()
            reponse.release_conn()

        if not isinstance(evenement, dict):
            erreurs.append(f"{nom_objet} : format JSON incorrect")
            continue

        event_id = evenement.get("event_id")
        montant = evenement.get("amount")

        if not event_id:
            erreurs.append(f"{nom_objet} : event_id absent")
            continue

        if montant is None or isinstance(montant, bool):
            erreurs.append(f"{nom_objet} : amount absent ou invalide")
            continue

        try:
            from decimal import Decimal

            montant_decimal = Decimal(str(montant))

            if not montant_decimal.is_finite():
                raise ValueError("Montant non fini")
        except (ValueError, TypeError, ArithmeticError):
            erreurs.append(f"{nom_objet} : amount non numerique")
            continue

        if event_id in identifiants:
            erreurs.append(f"{nom_objet} : event_id en doublon")
            continue

        identifiants.add(event_id)

    if erreurs:
        raise RuntimeError(
            "Controle Silver en echec :\n" + "\n".join(erreurs[:20])
        )

    print(f"OK - {len(objets)} evenements Silver valides")
    print("OK - Aucun event_id duplique dans Silver")


# ============================================================
# TACHE 4 - CHARGER SILVER VERS POSTGRESQL
# ============================================================

def charger_postgresql():
    executer_script("silver_to_postgres.py")


# ============================================================
# TACHE 5 - VALIDATION FINALE
# ============================================================

def validation_finale():
    """Verifie la coherence des identifiants Silver / PostgreSQL."""
    client = get_minio_client()
    objets = lister_objets(client, SILVER_BUCKET)

    identifiants_silver = set()

    for nom_objet in objets:
        reponse = client.get_object(SILVER_BUCKET, nom_objet)

        try:
            evenement = json.loads(reponse.read())
        finally:
            reponse.close()
            reponse.release_conn()

        identifiants_silver.add(evenement["event_id"])

    connexion = psycopg2.connect(
        os.environ["DATABASE_URL"],
        connect_timeout=10,
    )

    try:
        with connexion.cursor() as curseur:
            curseur.execute(
                """
                SELECT event_id
                FROM streaming.transactions_e7
                """
            )
            identifiants_postgres = {
                ligne[0] for ligne in curseur.fetchall()
            }
    finally:
        connexion.close()

    manquants = identifiants_silver - identifiants_postgres

    if manquants:
        raise RuntimeError(
            f"{len(manquants)} evenements Silver absents de PostgreSQL"
        )

    print("OK - Tous les evenements Silver sont dans PostgreSQL")
    print(f"Evenements Silver : {len(identifiants_silver)}")
    print(f"Evenements PostgreSQL : {len(identifiants_postgres)}")
    print("OK - Validation finale reussie")


# ============================================================
# DEFINITION DU DAG AIRFLOW
# ============================================================

default_args = {
    "owner": "carrefour-data-engineering",
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}


with DAG(
    dag_id="carrefour_streaming_e7",
    description="Pipeline Kafka Bronze Silver PostgreSQL - E7",
    default_args=default_args,
    start_date=datetime(2026, 10, 1),
    schedule_interval=None,
    catchup=False,
    max_active_runs=1,
    tags=["carrefour", "e7", "streaming", "datamarket"],
) as dag:

    verifier_sources_minio = PythonOperator(
        task_id="verifier_sources_minio",
        python_callable=verifier_sources,
    )

    bronze_vers_silver = PythonOperator(
        task_id="bronze_vers_silver",
        python_callable=executer_script,
        op_kwargs={"nom_script": "bronze_to_silver.py"},
        execution_timeout=timedelta(minutes=10),
    )

    controler_qualite_silver_task = PythonOperator(
        task_id="controler_qualite_silver",
        python_callable=controler_qualite_silver,
    )

    silver_vers_postgresql = PythonOperator(
        task_id="silver_vers_postgresql",
        python_callable=charger_postgresql,
        execution_timeout=timedelta(minutes=10),
    )

    validation_finale_task = PythonOperator(
        task_id="validation_finale",
        python_callable=validation_finale,
    )

    verifier_sources_minio >> bronze_vers_silver

    bronze_vers_silver >> [
        controler_qualite_silver_task,
        silver_vers_postgresql,
    ]

    [
        controler_qualite_silver_task,
        silver_vers_postgresql,
    ] >> validation_finale_task
