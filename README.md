# Data Market – Simulation d’un système de données retail

Ce projet simule un système de données pour une grande distribution (type Carrefour).  
L'objectif est de construire une architecture data permettant de collecter, transformer et exploiter des données clients, transactions et produits.

## Objectifs du projet

- Construire un modèle de données retail réaliste
- Simuler un système de fidélité
- Mettre en place un pipeline de données
- Permettre l'analyse du comportement client

## Dataset utilisé

Le projet utilise le dataset public **Olist E-commerce** qui a été adapté pour simuler un environnement retail.

Transformations principales :
- création de foyers clients
- simulation de cartes de fidélité
- transformation des commandes en transactions
- génération de quantités réalistes
- simplification des moyens de paiement

## Modèle de données

Le modèle comprend les entités suivantes :

- **Foyers**
- **Customers**
- **Loyalty_cards**
- **Transactions**
- **Transaction_items**
- **Products**
- **Product_categories**

Les diagrammes MCD et MLD sont disponibles dans le dossier :
**diagrams**

## Gold Layer

La couche Gold contient des vues analytiques construites à partir des tables Silver.

### Vues disponibles

- transaction_amount : montant total d'une transaction
- customer_value : valeur d'un client
- foyer_rfm_metrics : métriques RFM par foyer
- foyer_rfm_segments : segmentation marketing des foyers


## Architecture Data

Ce projet suit une architecture Medallion :

- **Bronze** : données brutes et nettoyage dans les notebooks
- **Silver** : tables normalisées dans PostgreSQL
- **Gold** : vues analytiques et segmentation RFM


## Structure du projet

projet-carrefour/

├── data/  
│   ├── archive/                 ( dataset original Olist )  
│   └── outputs/                 ( fichiers CSV générés pour alimenter la base (couche Silver))

├── notebooks/                   ( nettoyage et préparation des données (Bronze))

├── scripts/
│   └── exports/                 ( scripts Python générant les tables Silver à partir des données nettoyées )

├── sql/
│   └── gold/                    ( vues analytiques (couche Gold) )

├── init/                        ( scripts SQL de création du schéma PostgreSQL (tables Silver) )

├── diagrams/                    ( MCD et MLD du modèle de données )

├── docker-compose.yml           ( infrastructure PostgreSQL via Docker )

└── README.md

## Technologies utilisées

- Python
- Pandas
- PostgreSQL
- Docker
- Git
- Jupyter Notebook