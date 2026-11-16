# Guide de mise en place – Corrections E7

Dézipper à la racine de `projet-carrefour`. Toutes les commandes se lancent dans PowerShell, **depuis la racine du projet**.

## 0. Préparation

Ajouter dans `.env` (mots de passe de 8 caractères minimum, sans accents) :

```
MINIO_PWD_INGESTION=...
MINIO_PWD_DATA_ENGINEER=...
MINIO_PWD_ANALYST=...
MINIO_PWD_AUDITOR=...
RGPD_DATABASE_URL=postgresql://svc_rgpd:MOT_DE_PASSE_RGPD@postgres:5432/datamarket_carrefour
```

Si PowerShell bloque les scripts : `Set-ExecutionPolicy -Scope Process Bypass`

## 1. Droits sur le Data Lake MinIO (C21)

```powershell
.\scripts\governance\setup_minio_iam.ps1
.\scripts\governance\test_minio_iam.ps1
```
📸 **Capture 1** : sortie de `mc admin group info` (groupes, membres, politiques)
📸 **Capture 2** : tableau des 14 tests (14 / 14 OK)

## 2. Cycle de vie automatique (C20)

```powershell
.\scripts\governance\setup_minio_lifecycle.ps1
```
📸 **Capture 3** : `mc ilm rule ls` (règles d'expiration actives)

## 3. Comptes PostgreSQL individuels et compte RGPD (C21)

Utiliser pour `pwd_rgpd` le **même mot de passe** que dans `RGPD_DATABASE_URL`.

```powershell
docker exec -it datamarket_carrefour_pg psql -U soufia -d datamarket_carrefour -v pwd_engineer=XXX -v pwd_analyst=XXX -v pwd_marketing=XXX -v pwd_auditeur=XXX -v pwd_api=XXX -v pwd_rgpd=XXX -f /sql/security/04_rbac_users_comptes.sql
```
📸 **Capture 4** : tableau « compte individuel → rôle collectif »

## 4. Catalogue dans PostgreSQL et droits de recherche (C20 / C21)

```powershell
python scripts\catalogue_minio.py
python scripts\enrichir_catalogue.py
docker cp catalogue\catalogue_metier.csv datamarket_carrefour_pg:/tmp/catalogue_metier.csv
docker exec -it datamarket_carrefour_pg psql -U soufia -d datamarket_carrefour -f /sql/catalogue/01_catalogue_schema.sql
docker exec -it datamarket_carrefour_pg psql -U soufia -d datamarket_carrefour -f /sql/catalogue/02_catalogue_tests.sql
```
📸 **Capture 5** : tableau des 7 tests de recherche dans le catalogue (7 / 7 OK)

## 5. Procédure RGPD (C20)

D'abord vérifier les dates des données :
```powershell
docker exec -it datamarket_carrefour_pg psql -U soufia -d datamarket_carrefour -c "SELECT MIN(transaction_timestamp), MAX(transaction_timestamp) FROM datamarket.transactions;"
```
⚠️ Si les transactions datent de plusieurs années, **tous** les clients seraient anonymisés avec la date du jour. Il faut alors utiliser une date de référence proche de la dernière transaction (par exemple `--date-ref 2018-10-31`).

```powershell
python scripts\rgpd\purge_clients_inactifs.py --date-ref AAAA-MM-JJ
```
📸 **Capture 6** : rapport de simulation (compte `svc_rgpd`, nombre de clients identifiés)

L'anonymisation réelle (`--execution`) est **irréversible**. Faire une sauvegarde avant :
```powershell
docker exec datamarket_carrefour_pg pg_dump -U soufia -d datamarket_carrefour -t datamarket.customers -f /tmp/customers_backup.sql
```

## 6. Supervision avec alertes (C20)

```powershell
python scripts\monitoring\check_datalake.py
```
📸 **Capture 7** : supervision normale (« Aucune alerte »)

Démonstration d'une rupture de service :
```powershell
docker stop phenix_minio
python scripts\monitoring\check_datalake.py
docker start phenix_minio
```
📸 **Capture 8** : `!!! ALERTE CRITIQUE - MinIO : ... rupture de service`

## 7. Planification Airflow

1. Remplacer `docker-compose.airflow.yml` par la version fournie (variables RGPD et supervision, dossier `logs` monté).
2. Copier `airflow/dags/carrefour_gouvernance_e7.py` dans `airflow/dags/`.
3. Dans `airflow/dags/carrefour_streaming_e7.py`, remplacer `schedule_interval=None` par `schedule_interval="@hourly"`. Le pipeline est idempotent (`ON CONFLICT DO NOTHING`), donc il peut tourner régulièrement.
4. Relancer Airflow, puis dans l'interface **Admin → Variables**, créer `RGPD_DATE_REF` si nécessaire (et `RGPD_EXECUTION=false` par défaut).

📸 **Capture 9** : liste des DAG avec leurs planifications (monitoring toutes les 10 min, RGPD mensuel, streaming horaire)
📸 **Capture 10** : DAG `carrefour_monitoring_e7` en échec rouge pendant que MinIO est arrêté

## 8. Fichiers à remplacer ou supprimer

- `sql/rgpd/cleanup.sql` : **à supprimer**. Il utilise des colonnes qui n'existent pas (`email`, `first_name`, `last_name`, `last_activity_date`) et il est remplacé par `scripts/rgpd/purge_clients_inactifs.py`.
