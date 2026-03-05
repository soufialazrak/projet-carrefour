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

## Structure du projet
projet-carrefour
│
├── data/ # données transformées
├── notebooks/ # nettoyage et préparation des données
├── scripts/ # scripts de transformation
├── diagrams/ # MCD et MLD
├── init/ # création du schéma PostgreSQL
└── docker-compose.yml

## Technologies utilisées

- Python
- Pandas
- PostgreSQL
- Docker
- Git
- Jupyter Notebook