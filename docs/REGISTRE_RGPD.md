# Registre des traitements de données personnelles – Projet PHENIX (Carrefour Data Market)

*Article 30 du RGPD – Données simulées (dataset Olist enrichi) – Environnement de démonstration*

## 1. Responsable du traitement

| Élément | Valeur |
|---|---|
| Responsable | Carrefour (contexte simulé) – Direction Data / Connaissance client |
| Référent RGPD / DPO | DPO Carrefour (contexte simulé) |
| Responsable technique | Data Engineer – Soufia LAZRAK |
| Date de mise à jour | Novembre 2026 |

## 2. Fiches de traitement

### Traitement n° 1 – Gestion du programme de fidélité

| Rubrique | Description |
|---|---|
| Finalité | Gérer les cartes de fidélité et rattacher les achats aux clients |
| Base légale | Exécution du contrat (adhésion au programme de fidélité) |
| Personnes concernées | Clients titulaires d'une carte de fidélité |
| Données traitées | Nom, prénom, e-mail (chiffrés), empreinte SHA-256 de l'e-mail, année de naissance, ville, code postal, région, identifiant de carte, statut et dates de la carte |
| Sources | Fichiers CSV historiques (Bronze `carrefour/`), exports préparés (Silver `e7/`) |
| Stockage | MinIO `phenix-bronze`, `phenix-silver` ; PostgreSQL `datamarket.customers`, `datamarket.loyalty_cards` |
| Destinataires internes | Data Engineers (traitement) ; API applicative (`svc_api`, lecture seule) |
| Durée de conservation | Durée de la relation commerciale + 24 mois d'inactivité, puis anonymisation |
| Transferts hors UE | Aucun (hébergement local) |

### Traitement n° 2 – Analyse des achats et segmentation RFM

| Rubrique | Description |
|---|---|
| Finalité | Analyser les comportements d'achat et segmenter les foyers (récence, fréquence, montant) |
| Base légale | Intérêt légitime (amélioration de l'offre), limité à des données pseudonymisées ou agrégées |
| Personnes concernées | Clients et foyers |
| Données traitées | Identifiants pseudonymes (`customer_id`, `household_id`), transactions, montants, produits |
| Stockage | PostgreSQL `datamarket.transactions`, `transaction_items` ; vues `gold.*` |
| Destinataires internes | Data Analysts (vues Gold) ; Marketing (synthèse agrégée uniquement) |
| Durée de conservation | Transactions : 10 ans (obligations comptables) ; les identités sont anonymisées après 24 mois d'inactivité |

### Traitement n° 3 – Collecte des transactions en temps réel

| Rubrique | Description |
|---|---|
| Finalité | Intégrer les transactions en continu pour le suivi de l'activité |
| Base légale | Exécution du contrat |
| Données traitées | Identifiant d'événement, montant, horodatage, identifiants pseudonymes |
| Stockage | Redpanda (topic `phenix.transactions.e7`) ; MinIO `streaming/` ; PostgreSQL `streaming.transactions_e7` |
| Durée de conservation | Bronze `streaming/` : 30 jours ; Silver `streaming/` : 90 jours (règles ILM MinIO automatiques) |

## 3. Mesures de sécurité (communes)

| Mesure | Mise en œuvre |
|---|---|
| Chiffrement applicatif | Nom, prénom et e-mail chiffrés (clé `DATA_ENCRYPTION_KEY`) |
| Pseudonymisation | Empreinte SHA-256 de l'e-mail, identifiants techniques |
| Contrôle d'accès – Data Lake | Groupes MinIO et politiques ; lecture de `customers.csv` et `loyalty_cards.csv` interdite aux analystes |
| Contrôle d'accès – Base | Rôles PostgreSQL collectifs ; schéma `datamarket` inaccessible aux analystes et au marketing |
| Contrôle d'accès – Catalogue | Row Level Security : les analystes ne voient pas les objets Bronze |
| Secrets | Fichier `.env` exclu du dépôt Git ; aucun mot de passe dans les scripts |
| Traçabilité | Journalisation des connexions PostgreSQL ; journal des purges `rgpd.journal_purge` |
| Supervision | Contrôle automatique toutes les 10 minutes, avec alertes |

## 4. Procédure de tri des données personnelles

| Étape | Traitement | Automatisé | Fréquence |
|---|---|---|---|
| 1 | Identification des clients inactifs depuis plus de 24 mois (dernière transaction, dernière utilisation de carte) | Oui – DAG `carrefour_rgpd_e7` | Mensuelle (le 1er à 03h00) |
| 2 | Revue du nombre de clients identifiés et des obligations de conservation | Non – Data Engineer + référent RGPD | Mensuelle |
| 3 | Anonymisation : nom, prénom, e-mail, empreinte, année de naissance, ville et code postal mis à NULL | Oui, après validation (`RGPD_EXECUTION=true`) | Mensuelle |
| 4 | Traçabilité : enregistrement de chaque passage dans `rgpd.journal_purge` | Oui | À chaque exécution |
| 5 | Purge des événements bruts du flux temps réel | Oui – règles ILM MinIO | Continue (30 / 90 jours) |
| 6 | Suppression des fichiers de test techniques | Oui – règles ILM MinIO | Continue (7 jours) |
| 7 | Demande d'effacement d'un client (article 17) | Non – traitement manuel ciblé par `customer_id` | Sous 1 mois après la demande |
| 8 | Revue du registre et des droits d'accès | Non | Annuelle |
