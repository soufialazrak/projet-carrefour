# Gouvernance des accès au Data Lake MinIO – Projet PHENIX (E7 / C21)

## 1. Principe

- Les droits sont attribués à des **groupes**, jamais directement à des utilisateurs.
- Chaque groupe ne reçoit que les droits nécessaires à sa mission (**moindre privilège**).
- Les comptes de service (ingestion) sont séparés des comptes humains.
- Les fichiers contenant des **données personnelles** (`customers.csv`, `loyalty_cards.csv`) sont explicitement interdits en lecture aux analystes (règle `Deny`, RGPD).
- Aucun mot de passe n'est écrit dans les scripts : ils sont lus dans `.env`, exclu du dépôt Git.

## 2. Les trois types de droits

| Type de droit | Action S3 | Signification |
|---|---|---|
| Alimentation | `s3:PutObject` (+ `s3:DeleteObject`) | déposer ou supprimer des données dans le lake |
| Index / recherche | `s3:ListBucket` | lister et rechercher les objets d'une couche |
| Récupération | `s3:GetObject` | télécharger le contenu d'un objet |

## 3. Groupes, politiques et utilisateurs

| Groupe | Politique | Utilisateur(s) | Usage |
|---|---|---|---|
| `grp-ingestion` | `pol-ingestion` | `svc_ingestion` (compte de service) | dépôt des données brutes (batch et streaming) |
| `grp-data-engineer` | `pol-data-engineer` | `de_soufia` | transformation Bronze → Silver, maintenance, cycle de vie |
| `grp-data-analyst` | `pol-data-analyst` | `analyst_demo` | consultation et récupération des données préparées |
| `grp-auditor` | `pol-auditor` | `auditor_demo` | contrôle de l'inventaire, sans accès au contenu |

## 4. Matrice des droits

| Groupe | Bronze | Silver | Gold | Données personnelles |
|---|---|---|---|---|
| Ingestion | Alimentation + index (+ lecture de `streaming/` seul, contrôle anti-doublon) | – | – | – |
| Data Engineer | Alimentation + index + récupération | Alimentation + index + récupération | Alimentation + index + récupération | Oui (traitement) |
| Data Analyst | – | Index + récupération | Index + récupération | **Refusé** |
| Auditeur | Index seul | Index seul | Index seul | – |

## 5. Droits individuels

Aucun droit n'est attaché directement à un utilisateur. Un utilisateur hérite uniquement des droits de son groupe. Le compte `root` MinIO (`MINIO_ROOT_USER`) est réservé à l'administration et n'est utilisé par aucun traitement applicatif.

## 6. Procédure de mise à jour des règles

1. **Demande** : le responsable métier formule une demande (nouvel utilisateur, nouveau besoin d'accès).
2. **Validation** : le Data Engineer vérifie la conformité (moindre privilège, RGPD) ; pour un accès à des données personnelles, validation par le référent RGPD.
3. **Modification** : mise à jour du fichier JSON dans `scripts/governance/policies/` (versionné dans Git) ou ajout de l'utilisateur au groupe dans `setup_minio_iam.ps1`.
4. **Application** : exécution de `setup_minio_iam.ps1` (le script est rejouable).
5. **Contrôle** : exécution de `test_minio_iam.ps1`, puis archivage du résultat (`catalogue/tests_droits_minio.csv`).
6. **Révocation** : départ d'un collaborateur → `mc admin user disable local <utilisateur>`, puis suppression.
7. **Revue périodique** : revue trimestrielle des membres de chaque groupe (`mc admin group info`).
