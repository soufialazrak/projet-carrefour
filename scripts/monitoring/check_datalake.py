"""
CARREFOUR DATAMARKET - E7
Supervision du Data Lake avec ALERTES (C20).

Controles :
  - MinIO       : disponibilite (HTTP /minio/health/live) + volume par bucket
  - PostgreSQL  : connexion, taille de la base, nombre de lignes des tables
  - Redpanda    : broker joignable
  - Conteneurs  : etat, CPU et memoire (uniquement depuis le poste hote,
                  ou la commande docker voit les conteneurs)

Fichiers produits dans logs/ (lus par la page Streamlit "Supervision") :
  - monitoring_dernier_controle.json : resultat du dernier controle
  - monitoring_docker.json           : derniere mesure des conteneurs (poste hote)
  - alertes_monitoring.log           : historique des alertes

Si un seuil est depasse ou un service ne repond pas :
  - une alerte est ecrite dans logs/alertes_monitoring.log
  - elle est enregistree dans la table monitoring.alertes (si PostgreSQL repond)
  - le script se termine avec le code 1 -> la tache Airflow passe en echec

Usage (racine du projet) :
  python scripts/monitoring/check_datalake.py
Demonstration d'une rupture de service :
  docker stop phenix_minio ; python scripts/monitoring/check_datalake.py ; docker start phenix_minio
"""
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import urllib.request
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import psycopg2
from minio import Minio

ROOT = Path(__file__).resolve().parents[2]
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass

DANS_DOCKER = os.environ.get("RUNNING_IN_DOCKER") == "1"
MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT", "localhost:9000")
REDPANDA = os.environ.get("REDPANDA_BOOTSTRAP",
                          "redpanda:9092" if DANS_DOCKER else "localhost:19092")
BUCKETS = ["phenix-bronze", "phenix-silver", "phenix-gold"]
CONTENEURS = ["phenix_minio", "datamarket_carrefour_pg", "phenix_redpanda_e7",
              "datamarket_carrefour_api", "datamarket_carrefour_streamlit",
              "projet-carrefour-airflow-1", "projet-carrefour-airflow-db-1"]
TABLES = ["product_categories", "products", "households", "loyalty_cards",
          "customers", "transactions", "transaction_items"]

# Seuils d'alerte
SEUIL_BUCKET_MO = 5 * 1024        # 5 Go par bucket
SEUIL_MEMOIRE_PCT = 80.0          # % de memoire d'un conteneur
SEUIL_CPU_PCT = 90.0
LOG_DIR = Path(os.environ.get("MONITORING_LOG_DIR", ROOT / "logs"))

resultats = []   # (composant, controle, valeur, statut)
alertes = []     # (niveau, composant, message)
mesures = {"minio": {"disponible": False, "http": None, "buckets": {}},
           "postgresql": {"disponible": False, "taille_base": None, "tables": {}},
           "redpanda": {"disponible": False, "broker": REDPANDA}}
conteneurs = []  # mesures Docker (poste hote uniquement)


def ok(composant, controle, valeur):
    resultats.append((composant, controle, valeur, "OK"))


def alerte(composant, controle, valeur, message, niveau="CRITIQUE"):
    resultats.append((composant, controle, valeur, f"ALERTE {niveau}"))
    alertes.append((niveau, composant, message))


def url_postgres():
    url = os.environ["DATABASE_URL"]
    if DANS_DOCKER:
        return url
    parts = urlsplit(url)
    identifiants = parts.netloc.rsplit("@", 1)[0] + "@" if "@" in parts.netloc else ""
    return urlunsplit(parts._replace(netloc=identifiants + "localhost:5433"))


def en_mio(texte):
    """Convertit '188.6MiB' ou '1.2GiB' en Mio."""
    m = re.match(r"([\d.]+)\s*([KMG]i?B)", texte.strip())
    if not m:
        return None
    facteur = {"KiB": 1 / 1024, "KB": 1 / 1024, "MiB": 1, "MB": 1, "GiB": 1024, "GB": 1024}
    return round(float(m.group(1)) * facteur.get(m.group(2), 1), 1)


def controler_minio():
    try:
        with urllib.request.urlopen(f"http://{MINIO_ENDPOINT}/minio/health/live", timeout=5) as r:
            ok("MinIO", "Disponibilite HTTP", r.status)
            mesures["minio"].update(disponible=True, http=r.status)
    except Exception as exc:
        alerte("MinIO", "Disponibilite HTTP", "aucune reponse",
               f"MinIO ne repond pas ({type(exc).__name__}) : rupture de service du stockage")
        return
    client = Minio(MINIO_ENDPOINT, access_key=os.environ["MINIO_ROOT_USER"],
                   secret_key=os.environ["MINIO_ROOT_PASSWORD"], secure=False)
    for bucket in BUCKETS:
        if not client.bucket_exists(bucket):
            alerte("MinIO", f"Bucket {bucket}", "absent", f"Bucket {bucket} introuvable",
                   niveau="MAJEURE")
            continue
        objets = [o for o in client.list_objects(bucket, recursive=True) if not o.is_dir]
        volume_mo = sum(o.size or 0 for o in objets) / 1024 / 1024
        mesures["minio"]["buckets"][bucket] = {"objets": len(objets), "volume_mo": round(volume_mo, 1)}
        valeur = f"{len(objets)} objets / {volume_mo:.1f} Mo"
        if volume_mo > SEUIL_BUCKET_MO:
            alerte("MinIO", f"Volume {bucket}", valeur,
                   f"Volume de {bucket} superieur a {SEUIL_BUCKET_MO} Mo", niveau="MAJEURE")
        else:
            ok("MinIO", f"Volume {bucket}", valeur)


def controler_postgres():
    try:
        connexion = psycopg2.connect(url_postgres(), connect_timeout=5)
        with connexion.cursor() as cur:
            cur.execute("SELECT pg_size_pretty(pg_database_size(current_database()))")
            taille = cur.fetchone()[0]
            ok("PostgreSQL", "Connexion / taille base", taille)
            mesures["postgresql"].update(disponible=True, taille_base=taille)
            for table in TABLES:
                try:
                    cur.execute(f"SELECT COUNT(*) FROM datamarket.{table}")
                    mesures["postgresql"]["tables"][table] = cur.fetchone()[0]
                except Exception:
                    connexion.rollback()
        connexion.close()
    except Exception as exc:
        alerte("PostgreSQL", "Connexion", "echec",
               f"PostgreSQL injoignable ({type(exc).__name__}) : rupture de service")


def controler_redpanda():
    hote, port = REDPANDA.rsplit(":", 1)
    try:
        with socket.create_connection((hote, int(port)), timeout=5):
            ok("Redpanda", f"Broker {REDPANDA}", "joignable")
            mesures["redpanda"]["disponible"] = True
    except OSError:
        alerte("Redpanda", f"Broker {REDPANDA}", "injoignable",
               "Broker Redpanda injoignable : flux temps reel interrompu")


def controler_conteneurs():
    if DANS_DOCKER or shutil.which("docker") is None:
        resultats.append(("Docker", "Conteneurs", "controle depuis le poste hote", "NON CONTROLE"))
        return
    etats = subprocess.run(["docker", "ps", "-a", "--format", "{{json .}}"],
                           capture_output=True, text=True, timeout=30).stdout.splitlines()
    etats = {json.loads(l)["Names"]: json.loads(l)["State"] for l in etats if l.strip()}
    stats = subprocess.run(["docker", "stats", "--no-stream", "--format", "{{json .}}"],
                           capture_output=True, text=True, timeout=60).stdout.splitlines()
    stats = {json.loads(l)["Name"]: json.loads(l) for l in stats if l.strip()}
    for nom in CONTENEURS:
        etat = etats.get(nom, "absent")
        if etat != "running":
            alerte("Docker", nom, etat, f"Conteneur {nom} arrete (etat : {etat})")
            conteneurs.append({"conteneur": nom, "etat": etat, "cpu_pct": None,
                               "ram_mio": None, "ram_pct": None, "statut": "ALERTE"})
            continue
        s = stats.get(nom, {})
        cpu = float(s.get("CPUPerc", "0%").rstrip("%") or 0)
        mem = float(s.get("MemPerc", "0%").rstrip("%") or 0)
        ram = en_mio(s.get("MemUsage", "").split("/")[0]) if s.get("MemUsage") else None
        valeur = f"CPU {cpu:.1f} % / RAM {s.get('MemUsage', '?')} ({mem:.1f} %)"
        statut = "OK"
        if mem > SEUIL_MEMOIRE_PCT or cpu > SEUIL_CPU_PCT:
            alerte("Docker", nom, valeur, f"Ressources de {nom} au-dessus des seuils",
                   niveau="MAJEURE")
            statut = "ALERTE"
        else:
            ok("Docker", nom, valeur)
        conteneurs.append({"conteneur": nom, "etat": etat, "cpu_pct": cpu,
                           "ram_mio": ram, "ram_pct": mem, "statut": statut})


def enregistrer_alertes(horodatage):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with (LOG_DIR / "alertes_monitoring.log").open("a", encoding="utf-8") as f:
        for niveau, composant, message in alertes:
            f.write(f"{horodatage} [{niveau}] {composant} - {message}\n")
    try:
        connexion = psycopg2.connect(url_postgres(), connect_timeout=5)
        with connexion, connexion.cursor() as cur:
            cur.execute("""
                CREATE SCHEMA IF NOT EXISTS monitoring;
                CREATE TABLE IF NOT EXISTS monitoring.alertes (
                    id SERIAL PRIMARY KEY,
                    detectee_le TIMESTAMP NOT NULL,
                    niveau TEXT NOT NULL,
                    composant TEXT NOT NULL,
                    message TEXT NOT NULL)""")
            cur.executemany(
                "INSERT INTO monitoring.alertes (detectee_le, niveau, composant, message) "
                "VALUES (%s, %s, %s, %s)",
                [(horodatage, n, c, m) for n, c, m in alertes])
        connexion.close()
    except Exception:
        pass  # PostgreSQL lui-meme en panne : l'alerte reste dans le fichier log


def main():
    maintenant = datetime.now().astimezone()
    horodatage = maintenant.strftime("%Y-%m-%d %H:%M:%S")
    controler_minio()
    controler_postgres()
    controler_redpanda()
    controler_conteneurs()

    print("=" * 92)
    print(f"SUPERVISION DU DATA LAKE - {horodatage}")
    print("=" * 92)
    for composant, controle, valeur, statut in resultats:
        print(f"{composant:<11} {controle:<32} {str(valeur):<34} {statut}")
    print("-" * 92)

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    origine = "Airflow (conteneur)" if DANS_DOCKER else "poste hote"
    (LOG_DIR / "monitoring_dernier_controle.json").write_text(json.dumps({
        "horodatage": horodatage,
        "horodatage_iso": maintenant.isoformat(timespec="seconds"),
        "origine": origine,
        "mesures": mesures,
        "resultats": [dict(zip(("composant", "controle", "valeur", "statut"), map(str, r))) for r in resultats],
        "alertes": [dict(zip(("niveau", "composant", "message"), a)) for a in alertes],
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    if conteneurs:
        (LOG_DIR / "monitoring_docker.json").write_text(json.dumps({
            "horodatage_iso": maintenant.isoformat(timespec="seconds"),
            "conteneurs": conteneurs,
        }, ensure_ascii=False, indent=2), encoding="utf-8")

    if alertes:
        enregistrer_alertes(horodatage)
        for niveau, composant, message in alertes:
            print(f"!!! ALERTE {niveau} - {composant} : {message}")
        print(f"{len(alertes)} alerte(s) enregistree(s) (logs/alertes_monitoring.log, monitoring.alertes)")
        return 1
    print("Aucune alerte - tous les services sont operationnels")
    return 0


if __name__ == "__main__":
    sys.exit(main())
