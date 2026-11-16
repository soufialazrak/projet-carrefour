"""
CARREFOUR DATAMARKET - E7
Planification de la supervision (C20) et de la procedure RGPD (C20 / C21).

DAG 1 - carrefour_monitoring_e7 : toutes les 10 minutes
    Controle MinIO, PostgreSQL et Redpanda. En cas de rupture de service,
    l'alerte est enregistree (log + table monitoring.alertes) et la tache
    passe en echec (rouge dans Airflow).

DAG 2 - carrefour_rgpd_e7 : le 1er de chaque mois a 03h00
    1. Simulation : compte les clients inactifs depuis plus de 24 mois.
    2. Anonymisation : executee seulement si la Variable Airflow
       RGPD_EXECUTION vaut "true" (validation humaine prealable,
       conformement a la procedure de tri RGPD).
    Variable optionnelle RGPD_DATE_REF (AAAA-MM-JJ) pour les donnees
    historiques ; sinon la date du jour est utilisee.
"""
import subprocess
import sys
from datetime import datetime, timedelta

from airflow import DAG
from airflow.models import Variable
from airflow.operators.python import PythonOperator, ShortCircuitOperator

SCRIPTS_DIR = "/opt/airflow/project/scripts"


def lancer(script, *arguments):
    subprocess.run([sys.executable, f"{SCRIPTS_DIR}/{script}", *arguments],
                   check=True, timeout=600)


def arguments_rgpd():
    date_ref = Variable.get("RGPD_DATE_REF", default_var="")
    return ["--date-ref", date_ref] if date_ref else []


def simulation_rgpd():
    lancer("rgpd/purge_clients_inactifs.py", *arguments_rgpd())


def execution_autorisee():
    autorise = Variable.get("RGPD_EXECUTION", default_var="false").lower() == "true"
    print("Anonymisation autorisee" if autorise
          else "Anonymisation non validee (RGPD_EXECUTION != true) : simulation seule")
    return autorise


def execution_rgpd():
    lancer("rgpd/purge_clients_inactifs.py", "--execution", *arguments_rgpd())


default_args = {"owner": "carrefour-data-engineering", "retries": 0}

with DAG(
    dag_id="carrefour_monitoring_e7",
    description="Supervision du Data Lake avec alertes - E7",
    default_args=default_args,
    start_date=datetime(2026, 11, 1),
    schedule_interval="*/10 * * * *",
    catchup=False,
    max_active_runs=1,
    dagrun_timeout=timedelta(minutes=5),
    tags=["carrefour", "e7", "monitoring"],
) as dag_monitoring:
    PythonOperator(
        task_id="controler_services_datalake",
        python_callable=lancer,
        op_args=["monitoring/check_datalake.py"],
    )

with DAG(
    dag_id="carrefour_rgpd_e7",
    description="Procedure RGPD mensuelle : clients inactifs > 24 mois - E7",
    default_args=default_args,
    start_date=datetime(2026, 11, 1),
    schedule_interval="0 3 1 * *",
    catchup=False,
    max_active_runs=1,
    tags=["carrefour", "e7", "rgpd", "gouvernance"],
) as dag_rgpd:
    simulation = PythonOperator(task_id="simulation_clients_inactifs",
                                python_callable=simulation_rgpd)
    validation = ShortCircuitOperator(task_id="validation_execution",
                                      python_callable=execution_autorisee)
    anonymisation = PythonOperator(task_id="anonymisation_clients_inactifs",
                                   python_callable=execution_rgpd)
    simulation >> validation >> anonymisation
