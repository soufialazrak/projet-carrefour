# Data Lineage — Carrefour Data Market — E7



**Projet :** Carrefour Data Market  

**Formation :** Data Engineer — Simplon  

**Bloc :** Bloc 4 — E7  

**Objet :** Traçabilité des données, transformations, contrôles qualité et orchestration du pipeline streaming.



---



## 1. Objectif du document



Ce document présente la traçabilité des événements transactionnels du pipeline E7.



Il permet d'identifier :



- Les sources des événements.

- Les composants techniques utilisés.

- Les transformations appliquées.

- Les contrôles de qualité.

- Les règles de gestion des doublons.

- Les destinations des données.

- Les limites techniques et les améliorations possibles.



Le pipeline streaming E7 est distinct du traitement historique des transactions utilisé pour la segmentation RFM.



## 2. Architecture générale



Le parcours des données est le suivant :



```text

Producteur Python

&#x20;      |

&#x20;      v

Redpanda / Kafka

Topic : phenix.transactions.e7

&#x20;      |

&#x20;      v

consumer_to_bronze.py

&#x20;      |

&#x20;      v

MinIO Bronze

phenix-bronze/streaming/transactions/

&#x20;      |

&#x20;      v

bronze_to_silver.py

&#x20;      |

&#x20;      v

MinIO Silver

phenix-silver/streaming/transactions/

&#x20;      |

&#x20;      v

silver_to_postgres.py

&#x20;      |

&#x20;      v

PostgreSQL

streaming.transactions_e7

&#x20;      |

&#x20;      v

streaming.audit_transactions_summary

```



Le producteur et le consommateur Kafka sont exécutés séparément du DAG Airflow.



Airflow orchestre les traitements à partir de la vérification des fichiers présents dans MinIO Bronze.



## 3. Source des données — Producteur Python



**Scripts :**



- `scripts/e7_streaming/producer_transactions.py`

- `scripts/e7_streaming/producer_transactions_confluent.py`



Ces scripts génèrent des transactions fictives destinées à la démonstration E7.



Chaque exécution produit cinq événements.



Les deux scripts utilisent le même topic Kafka :



`phenix.transactions.e7`



### Structure d'un événement



| Champ | Description |

|---|---|

| event_id | Identifiant unique de l'événement, au format UUID |

| transaction_id | Identifiant de la transaction fictive |

| event_timestamp | Date et heure de l'événement |

| amount | Montant de la transaction |

| currency | Devise |

| channel | Canal de transaction |

| source | Origine de l'événement |



Les valeurs générées comprennent :



- Une devise `EUR`.

- Un canal `online` ou `store`.

- Une source `phenix-e7-simulation`.

- Un horodatage UTC.

- Un montant compris entre 15,50 € et 64,50 €.



Ces événements sont simulés. Ils ne proviennent pas directement d'un système transactionnel Carrefour.



## 4. Transport des événements — Redpanda



**Technologie :** Redpanda, compatible avec l'API Kafka.



**Topic :** `phenix.transactions.e7`



**Broker accessible depuis Windows :** `localhost:19092`



Le producteur publie les événements JSON dans le topic.



Deux implémentations sont disponibles :



- `kafka-python`, avec attente de confirmation pour chaque envoi.

- `confluent-kafka`, avec utilisation d'une clé Kafka correspondant à `event_id` et vérification des messages restants après `flush`.



Les producteurs utilisent `acks=all`.



## 5. Ingestion Kafka vers MinIO Bronze



**Script :** `scripts/e7_streaming/consumer_to_bronze.py`



**Groupe consommateur :** `phenix-e7-bronze-v1`



**Destination :** `phenix-bronze/streaming/transactions/`



Le consommateur :



1\. Lit les messages du topic Kafka.

2\. Décode leur contenu JSON.

3\. Vérifie la présence des sept champs obligatoires.

4\. Vérifie le format UUID de `event_id`.

5\. Vérifie le format de l'horodatage.

6\. Vérifie que le montant est numérique, non booléen et compris entre 0 inclus et 1 000 000 exclu.

7\. Construit le nom du fichier à partir de `event_id`.

8\. Vérifie si le fichier existe déjà dans Bronze.

9\. Stocke les nouveaux événements dans MinIO.

10\. Valide manuellement l'offset Kafka après le stockage ou la détection d'un doublon.



### Gestion des doublons



Chaque événement est enregistré sous la forme :



`streaming/transactions/{event_id}.json`



Si ce fichier existe déjà, le consommateur ne le réécrit pas.



### Limites



Le consommateur traite au maximum six messages nouveaux ou déjà présents par exécution.



Il s'agit d'un fonctionnement adapté à la démonstration, et non d'un consommateur continu de production.



Un événement invalide peut interrompre le traitement.



## 6. Transformation Bronze vers Silver



**Script :** `scripts/e7_streaming/bronze_to_silver.py`



**Source :** `phenix-bronze/streaming/transactions/`



**Destination :** `phenix-silver/streaming/transactions/`



### Règles de transformation



| Champ | Règle |

|---|---|

| event_id | Validation et normalisation UUID |

| transaction_id | Conversion en chaîne, suppression des espaces, valeur non vide |

| event_timestamp | Validation, fuseau horaire obligatoire, conversion UTC |

| amount | Conversion Decimal, montant fini, positif ou nul, inférieur à 1 000 000, maximum deux décimales |

| currency | Conversion en majuscules, valeur `EUR` obligatoire |

| channel | Conversion en minuscules, valeur `online` ou `store` obligatoire |

| source | Conversion en chaîne, suppression des espaces, valeur non vide |



Les sept champs sont obligatoires.



Le script produit un objet JSON normalisé contenant ces sept champs.



### Gestion des événements invalides



Lorsqu'un événement ne respecte pas les règles, il est rejeté et un message est affiché dans les logs.



Le script comptabilise :



- Les événements valides.

- Les événements rejetés.



Les événements rejetés ne sont pas enregistrés dans un bucket de quarantaine dédié.



### Nommage Silver



Chaque fichier valide est enregistré sous la forme :



`streaming/transactions/{event_id}.json`



Une nouvelle exécution peut réécrire un objet Silver portant le même identifiant.



## 7. Contrôle qualité Silver



Le DAG Airflow contient une tâche dédiée :



`controler_qualite_silver`



Cette tâche vérifie :



- La présence d'événements JSON dans Silver.

- La structure JSON de chaque événement.

- La présence de `event_id`.

- La présence d'un montant numérique fini.

- L'absence de doublons de `event_id` parmi les fichiers examinés.



En cas d'erreur, la tâche échoue et transmet un message d'erreur à Airflow.



Ce contrôle est complémentaire aux validations plus strictes effectuées pendant la transformation Bronze vers Silver.



## 8. Chargement Silver vers PostgreSQL



**Script :** `scripts/e7_streaming/silver_to_postgres.py`



**Source :** `phenix-silver/streaming/transactions/`



**Destination :** `streaming.transactions_e7`



### Correspondance des champs



| Champ Silver | Colonne PostgreSQL |

|---|---|

| event_id | event_id |

| transaction_id | transaction_id |

| event_timestamp | event_timestamp |

| amount | amount |

| currency | currency |

| channel | channel |

| source | source |



La table PostgreSQL comporte également une colonne `ingested_at`, qui n'est pas fournie explicitement par le script d'insertion.



### Idempotence



L'insertion utilise :



```sql

ON CONFLICT (event_id) DO NOTHING

```



Cette règle empêche la création d'une deuxième ligne lorsque le même `event_id` existe déjà.



Elle permet de relancer le chargement sans dupliquer les événements existants.



### Gestion des erreurs



Le script utilise un `SAVEPOINT` pour chaque événement.



En cas d'erreur :



- L'insertion de l'événement concerné est annulée.

- Un message est écrit dans les logs.

- Le traitement peut continuer sur les événements suivants.



Le script affiche trois compteurs :



- `inseres`

- `deja_presents`

- `rejetes`



## 9. Orchestration Airflow



**DAG :** `carrefour_streaming_e7`



**Fichier :** `airflow/dags/carrefour_streaming_e7.py`



Le DAG contient cinq tâches.



| Tâche | Fonction |

|---|---|

| verifier_sources_minio | Vérification des buckets et des fichiers Bronze |

| bronze_vers_silver | Exécution de bronze_to_silver.py |

| controler_qualite_silver | Contrôle qualité des événements Silver |

| silver_vers_postgresql | Exécution de silver_to_postgres.py |

| validation_finale | Comparaison des identifiants Silver et PostgreSQL |



### Ordre d'exécution



```text

verifier_sources_minio

&#x20;         |

&#x20;         v

&#x20;  bronze_vers_silver

&#x20;         |

&#x20;    +----+----+

&#x20;    |         |

&#x20;    v         v

controler_   silver_vers_

qualite_     postgresql

silver

&#x20;    |         |

&#x20;    +----+----+

&#x20;         |

&#x20;         v

&#x20;  validation_finale

```



Le contrôle qualité Silver et le chargement PostgreSQL sont exécutés en parallèle après la transformation Bronze vers Silver.



La validation finale attend la réussite des deux tâches.



### Configuration



- Déclenchement manuel : `schedule_interval=None`.

- Pas de rattrapage automatique des anciennes périodes : `catchup=False`.

- Une seule exécution active : `max_active_runs=1`.

- Une nouvelle tentative configurée en cas d'échec.

- Délai de deux minutes entre les tentatives.



Le DAG n'inclut pas directement le producteur Kafka ni le consommateur Kafka vers Bronze.



## 10. Validation finale



La tâche `validation_finale` :



1\. Récupère les `event_id` des fichiers Silver.

2\. Lit les `event_id` de `streaming.transactions_e7`.

3\. Compare les deux ensembles.

4\. Échoue si un identifiant Silver est absent de PostgreSQL.



Cette vérification permet de détecter des événements Silver non chargés.



Elle ne garantit pas, à elle seule, l'égalité des montants, des dates ou des autres attributs entre Silver et PostgreSQL.



Elle ne signale pas non plus les événements supplémentaires présents dans PostgreSQL.



## 11. Couche d'audit et indicateurs



**Vue PostgreSQL :** `streaming.audit_transactions_summary`



Cette vue fournit des indicateurs agrégés sur les événements stockés :



- `nombre_transactions`

- `identifiants_uniques`

- `montant_total`



Elle permet de consulter un résumé des données intégrées.



**Attention :** il s'agit d'une vue de synthèse des transactions, et non d'un journal d'audit des accès ou des modifications SQL.



## 12. Qualité, fiabilité et sécurité



### Contrôles implémentés



- Validation des champs obligatoires.

- Validation des identifiants UUID.

- Vérification des montants.

- Normalisation des dates et des formats.

- Détection des doublons.

- Insertion idempotente.

- Gestion des erreurs d'insertion par événement.

- Vérification finale des identifiants.

- Journalisation des résultats dans les logs des scripts et d'Airflow.



### Sécurité et accès



Les connexions MinIO et PostgreSQL utilisent des paramètres d'environnement.



Les rôles PostgreSQL et leurs permissions sont documentés séparément dans :



`sql/security/README.md`



Le dictionnaire des données est disponible dans :



`catalogue/dictionnaire_donnees.md`



La présence de rôles PostgreSQL ne signifie pas que tous les composants applicatifs utilisent déjà des comptes techniques distincts.



## 13. Limites et améliorations possibles



| Limite actuelle | Amélioration envisagée |

|---|---|

| Transactions simulées | Connexion à une source métier réelle |

| Consommateur limité à six messages | Consommation continue supervisée |

| Producteur et consommateur hors DAG | Orchestration ou supervision complémentaire |

| Rejets uniquement journalisés | Bucket de quarantaine et suivi des rejets |

| Contrôle final centré sur les identifiants | Contrôle des montants et autres attributs |

| Chargement et contrôle qualité Silver en parallèle | Contrôle bloquant avant chargement, selon les exigences métier |

| Documentation manuelle du lineage | Catalogue automatisé, par exemple OpenMetadata |

| Absence de preuve d'une traçabilité automatique complète | Centralisation des métriques, logs et alertes |



OpenMetadata est une piste d'évolution. Son installation et son fonctionnement ne sont pas considérés comme acquis dans l'environnement actuel.



## 14. Synthèse pour la soutenance E7



Le pipeline E7 illustre une architecture de traitement d'événements transactionnels reposant sur Redpanda, MinIO, Python, Airflow et PostgreSQL.



La traçabilité est assurée par l'identification des sources, des scripts de transformation, des destinations et des contrôles.



Les principaux mécanismes de fiabilité sont :



- La validation des événements.

- La normalisation Bronze vers Silver.

- La détection des doublons.

- L'insertion idempotente dans PostgreSQL.

- Le contrôle final des identifiants.



Cette architecture constitue une démonstration technique fonctionnelle sur des données simulées.



Les évolutions prioritaires concernent l'automatisation complète de l'ingestion, la gestion persistante des rejets, le renforcement de la supervision et l'intégration éventuelle d'un catalogue de métadonnées automatisé.



---



**Document :** `catalogue/data_lineage.md`  

**Périmètre :** Pipeline streaming Carrefour Data Market — E7  

**Statut :** Documentation établie à partir des scripts Python, du DAG Airflow et du schéma PostgreSQL examinés.

