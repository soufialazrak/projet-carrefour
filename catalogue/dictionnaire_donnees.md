

# Catalogue des données — Carrefour DataMarket E7

## 1. Objectif

Ce dictionnaire de données documente les objets PostgreSQL du projet Carrefour DataMarket E7 dans le cadre du rattrapage du Bloc 4.

Il permet de :

- Identifier les tables, vues et colonnes.

- Comprendre leur signification métier.

- Documenter les relations entre les données.

- Identifier les données personnelles et les mesures de protection.

- Retracer les dépendances entre les tables métier et les vues analytiques.

**Périmètre :** base PostgreSQL `datamarket_carrefour`, schémas `datamarket`, `gold` et `streaming`.

**Date de l'inventaire :** 02/11/2026.

**Source :** métadonnées et définitions SQL extraites de PostgreSQL.

## 2. Inventaire général

| Schéma | Objet | Type | Description métier |

|---|---|---|---|

| datamarket | customers | Table | Informations clients et rattachement aux foyers |

| datamarket | households | Table | Référentiel des foyers |

| datamarket | loyalty_cards | Table | Cartes de fidélité associées aux clients |

| datamarket | product_categories | Table | Catégories de produits |

| datamarket | products | Table | Référentiel produits |

| datamarket | transaction_items | Table | Lignes de produits achetés |

| datamarket | transactions | Table | Transactions associées aux cartes de fidélité |

| gold | customer_segmentation | Vue | Segmentation des clients selon leurs dépenses |

| gold | customer_value | Vue | Indicateurs de valeur par client |

| gold | household_rfm_metrics | Vue | Indicateurs RFM des foyers calculés à la date courante |

| gold | household_rfm_metrics_e7 | Vue | Indicateurs RFM des foyers avec date de référence fixe |

| gold | household_rfm_segments | Vue | Segmentation RFM des foyers à la date courante |

| gold | household_rfm_segments_e7 | Vue | Segmentation RFM reproductible pour E7 |

| gold | marketing_segments_summary | Vue | Synthèse agrégée des segments marketing |

| gold | transaction_amount | Vue | Montant calculé de chaque transaction |

| streaming | audit_transactions_summary | Vue | Synthèse agrégée des transactions de streaming |

| streaming | transactions_e7 | Table | Événements de transactions ingérés par le pipeline E7 |

**Total : 17 objets, dont 8 tables et 9 vues, et 92 colonnes.**

## 3. Dictionnaire des colonnes — datamarket

### 3.1. datamarket.customers

**Description :** référentiel des clients, de leurs informations personnelles et de leur rattachement à un foyer.

| Colonne | Type PostgreSQL | Nullable | Description métier |

|---|---|---|---|

| customer_id | varchar | Non | Identifiant unique du client |

| household_id | varchar | Non | Identifiant du foyer auquel appartient le client |

| first_name_encrypted | text | Oui | Prénom stocké sous forme chiffrée |

| last_name_encrypted | text | Oui | Nom stocké sous forme chiffrée |

| birth_year | integer | Oui | Année de naissance du client |

| email_encrypted | text | Oui | Adresse électronique stockée sous forme chiffrée |

| email_hash | varchar | Oui | Empreinte de l'adresse électronique |

| customer_city | varchar | Oui | Ville de résidence du client |

| postal_code | varchar | Oui | Code postal du client |

| region | varchar | Oui | Région géographique du client |

**Clé primaire :** `customer_id`.

**Clé étrangère :** `household_id` vers `datamarket.households`.

**Classification proposée :** données personnelles — accès restreint.

### 3.2. datamarket.households

**Description :** référentiel des foyers utilisés pour la segmentation marketing.

| Colonne | Type | Nullable | Description métier |

|---|---|---|---|

| household_id | varchar | Non | Identifiant unique du foyer |

| household_created_at | timestamp | Non | Date et heure de création du foyer |

**Clé primaire :** `household_id`.

**Classification proposée :** identifiants pseudonymes — accès contrôlé.

### 3.3. datamarket.loyalty_cards

**Description :** cartes de fidélité rattachées aux clients.

| Colonne | Type | Nullable | Description métier |

|---|---|---|---|

| card_id | varchar | Non | Identifiant unique de la carte |

| customer_id | varchar | Non | Identifiant du client titulaire |

| card_status | varchar | Non | Statut de la carte |

| issued_at | timestamp | Oui | Date et heure d'émission |

| last_used_at | timestamp | Oui | Date et heure de dernière utilisation |

**Clé primaire :** `card_id`.

**Clé étrangère :** `customer_id` vers `datamarket.customers`.

**Classification proposée :** données de fidélité associables à un client — accès contrôlé.

### 3.4. datamarket.product_categories

**Description :** nomenclature des catégories de produits.

| Colonne | Type | Nullable | Description métier |

|---|---|---|---|

| category_id | integer | Non | Identifiant unique de catégorie |

| category_name | varchar | Non | Libellé de la catégorie |

**Clé primaire :** `category_id`.

**Classification proposée :** données métier non personnelles.

### 3.5. datamarket.products

**Description :** référentiel des produits et de leurs caractéristiques physiques.

| Colonne | Type | Nullable | Description métier |

|---|---|---|---|

| product_id | varchar | Non | Identifiant unique du produit |

| category_id | integer | Non | Catégorie à laquelle appartient le produit |

| product_weight_g | numeric | Oui | Poids du produit en grammes |

| product_length_cm | numeric | Oui | Longueur du produit en centimètres |

| product_height_cm | numeric | Oui | Hauteur du produit en centimètres |

| product_width_cm | numeric | Oui | Largeur du produit en centimètres |

**Clé primaire :** `product_id`.

**Clé étrangère :** `category_id` vers `datamarket.product_categories`.

**Classification proposée :** données métier non personnelles.

### 3.6. datamarket.transaction_items

**Description :** détail des articles associés à chaque transaction.

| Colonne | Type | Nullable | Description métier |

|---|---|---|---|

| transaction_id | varchar | Non | Identifiant de la transaction |

| transaction_item_id | integer | Non | Identifiant de la ligne au sein de la transaction |

| product_id | varchar | Non | Produit concerné |

| quantity | integer | Non | Quantité achetée |

| unit_price | numeric | Non | Prix unitaire du produit |

**Clé primaire composée :** (`transaction_id`, `transaction_item_id`).

**Clés étrangères :**

- `transaction_id` vers `datamarket.transactions`.

- `product_id` vers `datamarket.products`.

**Classification proposée :** données transactionnelles pouvant être reliées à un client.

### 3.7. datamarket.transactions

**Description :** transactions commerciales enregistrées à partir des cartes de fidélité.

| Colonne | Type | Nullable | Description métier |

|---|---|---|---|

| transaction_id | varchar | Non | Identifiant unique de transaction |

| card_id | varchar | Non | Carte de fidélité utilisée |

| transaction_status | varchar | Oui | Statut de la transaction |

| channel | varchar | Oui | Canal de réalisation de la transaction |

| payment_types_used | varchar | Oui | Types de paiement utilisés |

| transaction_timestamp | timestamp | Non | Date et heure de la transaction |

**Clé primaire :** `transaction_id`.

**Clé étrangère :** `card_id` vers `datamarket.loyalty_cards`.

**Classification proposée :** données transactionnelles liées à un parcours client.

## 4. Dictionnaire des colonnes — gold

Les objets GOLD sont des vues PostgreSQL. Leur nullabilité est celle exposée par les métadonnées des vues ; elle ne signifie pas nécessairement que chaque résultat contient des valeurs nulles.

### 4.1. gold.customer_value

**Description :** calcul de la valeur commerciale de chaque client.

| Colonne | Type | Nullable | Description métier |

|---|---|---|---|

| customer_id | varchar | Oui | Identifiant du client |

| nb_transactions | bigint | Oui | Nombre de transactions distinctes |

| total_spent | numeric | Oui | Montant total des articles achetés |

| avg_item_price | numeric | Oui | Moyenne des montants calculés par ligne de transaction |

**Sources SQL :** `datamarket.customers`, `datamarket.loyalty_cards`, `datamarket.transactions`, `datamarket.transaction_items`.

### 4.2. gold.customer_segmentation

**Description :** segmentation commerciale des clients à partir de leurs dépenses.

| Colonne | Type | Nullable | Description métier |

|---|---|---|---|

| customer_id | varchar | Oui | Identifiant du client |

| nb_transactions | bigint | Oui | Nombre de transactions |

| total_spent | numeric | Oui | Montant total dépensé |

| avg_item_price | numeric | Oui | Moyenne des montants par ligne |

| customer_segment | text | Oui | Segment commercial attribué |

**Source SQL :** `gold.customer_value`.

**Règles de segmentation :**

- `Occasional` : `total_spent < 100`.

- `Regular` : `100 <= total_spent < 300`.

- `VIP` : `total_spent >= 300`.

### 4.3. gold.household_rfm_metrics

**Description :** indicateurs de récence, fréquence et montant par foyer, calculés à partir de `CURRENT_DATE`.

| Colonne | Type | Nullable | Description métier |

|---|---|---|---|

| household_id | varchar | Oui | Identifiant du foyer |

| last_purchase_date | date | Oui | Date du dernier achat |

| recency_days | integer | Oui | Nombre de jours depuis le dernier achat |

| frequency | bigint | Oui | Nombre de transactions distinctes |

| monetary | numeric | Oui | Somme des montants des articles achetés |

**Sources SQL :** `datamarket.customers`, `datamarket.loyalty_cards`, `datamarket.transactions`, `datamarket.transaction_items`.

### 4.4. gold.household_rfm_metrics_e7

**Description :** indicateurs RFM des foyers avec une date de référence fixe pour la démonstration E7.

| Colonne | Type | Nullable | Description métier |

|---|---|---|---|

| household_id | varchar | Oui | Identifiant du foyer |

| last_purchase_date | date | Oui | Date du dernier achat |

| recency_days | integer | Oui | Écart en jours entre le 27/10/2026 et le dernier achat |

| frequency | bigint | Oui | Nombre de transactions distinctes |

| monetary | numeric | Oui | Montant total des articles achetés |

**Date de référence SQL :** `2026-10-27`.

**Sources SQL :** les mêmes quatre tables métier que pour `gold.household_rfm_metrics`.

### 4.5. gold.household_rfm_segments

**Description :** classification des foyers selon les indicateurs RFM calculés à la date courante.

| Colonne | Type | Nullable | Description métier |

|---|---|---|---|

| household_id | varchar | Oui | Identifiant du foyer |

| last_purchase_date | date | Oui | Date du dernier achat |

| recency_days | integer | Oui | Récence en jours |

| frequency | bigint | Oui | Nombre de transactions |

| monetary | numeric | Oui | Montant total |

| recency_segment | text | Oui | Catégorie de récence |

| frequency_segment | text | Oui | Catégorie de fréquence |

| monetary_segment | text | Oui | Catégorie de montant |

| macro_segment | text | Oui | Segment marketing global |

**Source SQL :** `gold.household_rfm_metrics`.

### 4.6. gold.household_rfm_segments_e7

**Description :** classification RFM des foyers utilisée pour le scénario E7.

| Colonne | Type | Nullable | Description métier |

|---|---|---|---|

| household_id | varchar | Oui | Identifiant du foyer |

| last_purchase_date | date | Oui | Date du dernier achat |

| recency_days | integer | Oui | Récence calculée avec la date fixe E7 |

| frequency | bigint | Oui | Nombre de transactions |

| monetary | numeric | Oui | Montant total |

| recency_segment | text | Oui | Catégorie de récence |

| frequency_segment | text | Oui | Catégorie de fréquence |

| monetary_segment | text | Oui | Catégorie de montant |

| macro_segment | text | Oui | Segment marketing global |

**Source SQL :** `gold.household_rfm_metrics_e7`.

**Règles des macro-segments, dans l'ordre SQL :**

| Segment | Condition |

|---|---|

| Premium | Récence <= 90 jours, fréquence >= 4, montant >= 500 |

| Fideles | Récence <= 180 jours, fréquence >= 2, montant >= 250 |

| Fort potentiel | Récence <= 90 jours, montant >= 250 |

| A reactiver | Récence > 365 jours, fréquence >= 2 |

| Perdus | Récence > 365 jours, fréquence = 1 |

| Standard | Toutes les autres situations |

Les conditions sont évaluées dans cet ordre : la première condition satisfaite détermine le segment.

### 4.7. gold.marketing_segments_summary

**Description :** synthèse agrégée des foyers par segment marketing.

| Colonne | Type | Nullable | Description métier |

|---|---|---|---|

| macro_segment | text | Oui | Nom du segment marketing |

| nombre_foyers | bigint | Oui | Nombre de foyers du segment |

| pourcentage | numeric | Oui | Pourcentage des foyers appartenant au segment |

**Source SQL :** `gold.household_rfm_segments_e7`.

**Usage métier :** analyse de la répartition des foyers sans exposer leurs identifiants individuels.

### 4.8. gold.transaction_amount

**Description :** calcul du montant de chaque transaction et rattachement aux clients et foyers.

| Colonne | Type | Nullable | Description métier |

|---|---|---|---|

| transaction_id | varchar | Oui | Identifiant de transaction |

| customer_id | varchar | Oui | Client associé |

| household_id | varchar | Oui | Foyer associé |

| transaction_timestamp | timestamp | Oui | Date et heure de transaction |

| transaction_amount | numeric | Oui | Somme des quantités multipliées par les prix unitaires |

**Sources SQL :** `datamarket.transactions`, `datamarket.loyalty_cards`, `datamarket.customers`, `datamarket.transaction_items`.

## 5. Dictionnaire des colonnes — streaming

### 5.1. streaming.transactions_e7

**Description :** table d'ingestion des événements de transactions du pipeline de streaming E7.

| Colonne | Type | Nullable | Description métier |

|---|---|---|---|

| event_id | uuid | Non | Identifiant unique de l'événement |

| transaction_id | text | Non | Identifiant métier de la transaction |

| event_timestamp | timestamptz | Non | Date et heure de l'événement avec fuseau horaire |

| amount | numeric | Non | Montant de la transaction |

| currency | varchar | Non | Devise de la transaction |

| channel | varchar | Non | Canal de transaction |

| source | text | Non | Système ou origine déclarée de l'événement |

| ingested_at | timestamptz | Non | Date et heure d'ingestion dans PostgreSQL |

**Clé primaire :** `event_id`.

**Clé étrangère déclarée :** aucune.

**Classification proposée :** données transactionnelles de streaming, à accès contrôlé.

### 5.2. streaming.audit_transactions_summary

**Description :** vue agrégée de contrôle des transactions de streaming.

| Colonne | Type | Nullable | Description métier |

|---|---|---|---|

| nombre_transactions | bigint | Oui | Nombre total de lignes de transaction |

| identifiants_uniques | bigint | Oui | Nombre d'identifiants d'événements distincts |

| montant_total | numeric | Oui | Somme des montants de transaction |

**Usage :** contrôle agrégé du volume et des montants ingérés.

**Attention :** cette vue n'est pas un journal des connexions, des modifications ou des refus d'accès PostgreSQL.

## 6. Relations entre les tables

Les relations suivantes ont été identifiées à partir des contraintes de clés étrangères déclarées dans PostgreSQL.

| Table source | Colonne | Table référencée |

|---|---|---|

| customers | household_id | households |

| loyalty_cards | customer_id | customers |

| transactions | card_id | loyalty_cards |

| transaction_items | transaction_id | transactions |

| transaction_items | product_id | products |

| products | category_id | product_categories |

**Clé primaire composée :** `datamarket.transaction_items(transaction_id, transaction_item_id)`.

La table `streaming.transactions_e7` ne possède pas de clé étrangère déclarée vers les tables historiques.

## 7. Data lineage SQL

### 7.1. Segmentation RFM E7

```text

datamarket.customers

datamarket.loyalty_cards

datamarket.transactions

datamarket.transaction_items

&#x20;          |

&#x20;          v

gold.household_rfm_metrics_e7

&#x20;          |

&#x20;          v

gold.household_rfm_segments_e7

&#x20;          |

&#x20;          v

gold.marketing_segments_summary

```

### 7.2. Segmentation RFM classique

```text

Tables métier datamarket

&#x20;          |

&#x20;          v

gold.household_rfm_metrics

&#x20;          |

&#x20;          v

gold.household_rfm_segments

```

### 7.3. Segmentation client

```text

datamarket.customers

datamarket.loyalty_cards

datamarket.transactions

datamarket.transaction_items

&#x20;          |

&#x20;          v

gold.customer_value

&#x20;          |

&#x20;          v

gold.customer_segmentation

```

### 7.4. Calcul du montant des transactions

```text

datamarket.transactions

datamarket.loyalty_cards

datamarket.customers

datamarket.transaction_items

&#x20;          |

&#x20;          v

gold.transaction_amount

```

Ces dépendances sont confirmées par les définitions SQL des vues PostgreSQL.

Le lineage complet entre les fichiers MinIO, les traitements Airflow, PostgreSQL, FastAPI et Streamlit devra être documenté séparément à partir des fichiers de configuration et du code du projet.

## 8. Classification RGPD proposée

Cette classification est une proposition documentaire. Elle ne constitue pas, à elle seule, une preuve que tous les contrôles de sécurité sont appliqués.

| Données ou colonnes | Classification proposée | Mesure attendue |

|---|---|---|

| first_name_encrypted, last_name_encrypted | Données personnelles chiffrées | Chiffrement et accès restreint |

| email_encrypted | Donnée personnelle chiffrée | Chiffrement et accès restreint |

| email_hash | Donnée personnelle pseudonymisée | Contrôle d'accès et protection contre la réidentification |

| birth_year | Donnée personnelle | Minimisation des accès |

| customer_city, postal_code, region | Données de localisation approximative | Contrôle des accès et limitation des usages |

| customer_id, household_id, card_id | Identifiants pseudonymes | Limitation des accès et des rapprochements |

| Transactions associées à un client | Données comportementales | Accès limité aux finalités autorisées |

| Référentiel produits et catégories | Données métier non personnelles | Accès selon les besoins métier |

| marketing_segments_summary | Données agrégées | Vérification du risque de réidentification |

**Point important :** le hachage d'un email ne garantit pas son anonymisation. Un email haché peut rester une donnée personnelle.

## 9. Gouvernance et contrôle d'accès

Les rôles PostgreSQL documentés dans le projet sont :

| Rôle | Périmètre autorisé |

|---|---|

| role_data_analyst | Lecture des vues du schéma GOLD |

| role_marketing | Lecture de `gold.marketing_segments_summary` |

| role_data_engineer | Lecture et insertion dans `streaming.transactions_e7` |

| role_auditeur | Lecture de `streaming.audit_transactions_summary` |

Ces permissions ont été testées au niveau PostgreSQL.

**Limite :** les rôles fonctionnels ne constituent pas encore la preuve que les applications utilisent des comptes techniques distincts.

Références du projet :

- `sql/security/01_rbac_roles_permissions.sql`

- `sql/security/02_rbac_tests.sql`

- `sql/security/03_postgresql_audit.sql`

- `sql/security/README.md`

## 10. Limites et travaux complémentaires

L'inventaire présenté est issu des métadonnées PostgreSQL du 02/11/2026.

À ce stade :

1\. Aucun commentaire de colonne n'était enregistré dans PostgreSQL lors de la vérification.

2\. Les descriptions métier de ce document ont été rédigées à partir des noms des colonnes, des contraintes et des définitions SQL disponibles.

3\. La classification RGPD est proposée et doit être validée selon les règles de gouvernance du projet.

4\. Le lineage SQL des vues GOLD est identifié, mais le lineage de bout en bout reste à vérifier.

5\. Aucun service OpenMetadata n'a été identifié parmi les conteneurs Docker existants.

6\. Ce document constitue un dictionnaire de données versionné, et non une installation opérationnelle d'OpenMetadata.

## 11. Évolutions prévues

- Documenter les flux Bronze, Silver et Gold dans MinIO.

- Vérifier le pipeline Airflow et le streaming Redpanda.

- Ajouter les descriptions des jeux de données et leurs responsables.

- Compléter la classification des données sensibles.

- Préparer un schéma de lineage de bout en bout.

- Évaluer l'intégration dans OpenMetadata selon les ressources disponibles.

- Versionner les livrables du catalogue dans la branche `rattrapage-e7`.

## 12. Conclusion

Le catalogue documentaire constitue un premier socle de gouvernance des données pour Carrefour DataMarket E7.

Il recense les objets PostgreSQL, décrit leurs colonnes, identifie les relations entre les tables et retrace les principales transformations analytiques.

Il facilite la compréhension, la traçabilité et la sécurisation des données, tout en préparant leur intégration éventuelle dans un outil de catalogage.

