# Carrefour DataMarket — E7

## Documentation de sécurité PostgreSQL : RBAC et audit



### 1. Objectif



Cette documentation présente les mécanismes de sécurité mis en place dans le projet Carrefour DataMarket, dans le cadre de l'épreuve E7 : mise en production, exploitation et supervision.



Les objectifs sont :



- Limiter les accès aux données selon les responsabilités des utilisateurs.

- Appliquer le principe du moindre privilège.

- Vérifier les permissions PostgreSQL.

- Assurer la traçabilité des connexions et des erreurs d'autorisation.

- Fournir des preuves techniques vérifiables pour la soutenance.



### 2. Environnement technique



| Composant | Configuration |

|---|---|

| Projet | Carrefour DataMarket |

| Base de données | PostgreSQL 16 |

| Base PostgreSQL | `datamarket\_carrefour` |

| Conteneur Docker | `datamarket\_carrefour\_pg` |

| Service Docker Compose | `postgres` |

| Schémas concernés | `datamarket`, `gold`, `streaming` |

| Branche Git | `rattrapage-e7` |



L'environnement utilise Docker Compose pour exécuter PostgreSQL et les autres services du DataMarket.



### 3. Contrôle d'accès RBAC



Le RBAC (\*Role-Based Access Control\*) consiste à attribuer des permissions aux rôles selon leurs responsabilités.



Quatre rôles PostgreSQL ont été créés avec l'attribut `NOLOGIN`.



| Rôle | Permissions autorisées | Restrictions principales |

|---|---|---|

| `role\_data\_analyst` | Lecture des tables et vues du schéma `gold` | Pas d'accès aux données brutes du schéma `datamarket` |

| `role\_marketing` | Lecture de `gold.marketing\_segments\_summary` | Pas d'accès à la segmentation individuelle |

| `role\_data\_engineer` | Lecture et insertion dans `streaming.transactions\_e7` | Pas de modification ni de suppression des transactions |

| `role\_auditeur` | Lecture de `streaming.audit\_transactions\_summary` | Pas de lecture directe de `streaming.transactions\_e7` |



Les vues de synthèse permettent de fournir des informations agrégées sans exposer les données détaillées.



\*\*Limite actuelle :\*\* ces rôles ont été créés et testés au niveau PostgreSQL. Les applications utilisent encore un compte de connexion partagé. La mise en place de comptes techniques distincts reste une amélioration possible.



### 4. Tests de sécurité RBAC



Les permissions ont été vérifiées à l'aide du script :



`sql/security/02\_rbac\_tests.sql`



\*\*Résultat : 17 contrôles réussis sur 17.\*\*



Les tests ont notamment vérifié :



- Les accès autorisés aux vues et tables.

- Les accès interdits aux données individuelles.

- Les restrictions sur les opérations de modification.

- Les droits spécifiques au rôle Auditeur.



Les tests de refus d'accès ont été réalisés dans des transactions avec `ROLLBACK`, sans modification des données métier.



### 5. Preuves des refus d'accès PostgreSQL



Les journaux PostgreSQL du 30 octobre 2026 contiennent plusieurs refus d'accès correspondant aux tests RBAC.



#### Preuve 1 — Restriction du rôle Marketing



\*\*Horodatage :\*\* 2026-10-30 16:28:37 UTC



Requête testée :



```sql

BEGIN;

SET LOCAL ROLE role\_marketing;

SELECT customer\_id

FROM gold.customer\_segmentation

LIMIT 1;

ROLLBACK;

```



Résultat enregistré :



```text

ERROR: permission denied for view customer\_segmentation

```



\*\*Interprétation :\*\* le rôle Marketing ne peut pas consulter la vue de segmentation individuelle. Il doit utiliser la vue agrégée qui lui est autorisée.



#### Preuve 2 — Restriction du rôle Data Engineer



\*\*Horodatage :\*\* 2026-10-30 16:34:19 UTC



Requête testée :



```sql

BEGIN;

SET LOCAL ROLE role\_data\_engineer;

UPDATE streaming.transactions\_e7

SET amount = amount

WHERE FALSE;

ROLLBACK;

```



Résultat enregistré :



```text

ERROR: permission denied for table transactions\_e7

```



\*\*Interprétation :\*\* le rôle Data Engineer ne possède pas la permission `UPDATE` sur cette table.



Même si la condition `WHERE FALSE` ne sélectionne aucune ligne, PostgreSQL vérifie les permissions avant l'exécution de l'opération.



#### Preuve 3 — Restriction du rôle Auditeur



\*\*Horodatage :\*\* 2026-10-30 16:37:38 UTC



Requête testée :



```sql

BEGIN;

SET LOCAL ROLE role\_auditeur;

SELECT event\_id

FROM streaming.transactions\_e7

LIMIT 1;

ROLLBACK;

```



Résultat enregistré :



```text

ERROR: permission denied for table transactions\_e7

```



\*\*Interprétation :\*\* le rôle Auditeur ne peut pas consulter directement les transactions détaillées. Il dispose uniquement de la vue de synthèse autorisée.



#### Preuve complémentaire — Restriction du schéma datamarket



\*\*Horodatage :\*\* 2026-10-30 16:23:23 UTC



Le rôle `role\_data\_analyst` a tenté de consulter des colonnes de la table `datamarket.customers`.



Résultat :



```text

ERROR: permission denied for schema datamarket

```



Ce résultat confirme la séparation entre les données métier détaillées et les données analytiques autorisées.



### 6. Configuration de l'audit PostgreSQL



La configuration est documentée dans :



`sql/security/03\_postgresql\_audit.sql`



Les paramètres suivants ont été activés et vérifiés :



| Paramètre | Valeur |

|---|---|

| `log\_connections` | `on` |

| `log\_disconnections` | `on` |

| `log\_line\_prefix` | `%m \[%p] user=%u db=%d app=%a ` |

| `log\_destination` | `stderr` |



Cette configuration permet de retrouver les informations suivantes dans les journaux :



- Horodatage de l'événement.

- Identifiant du processus PostgreSQL.

- Utilisateur PostgreSQL.

- Base de données.

- Nom de l'application, lorsqu'il est renseigné.

- Connexions et déconnexions.



Les paramètres ont été rechargés avec `pg\_reload\_conf()`, sans redémarrage de PostgreSQL.



### 7. Preuves de journalisation



Le 2 novembre 2026, les journaux Docker ont confirmé la présence des événements suivants :



```text

LOG: connection received: host=\[local]

LOG: connection authorized: user=soufia database=datamarket\_carrefour application\_name=pg\_isready

LOG: disconnection: session time: 0:00:00.001 user=soufia database=datamarket\_carrefour host=\[local]

```



Ces événements correspondent au contrôle de santé PostgreSQL exécuté par Docker.



Ils démontrent que la journalisation des connexions et déconnexions fonctionne.



\*\*Précision :\*\* les erreurs de permissions observées le 30 octobre précèdent l'activation du nouveau format de journalisation. Elles démontrent l'enregistrement des refus d'accès, mais pas l'utilisation du nouveau préfixe sur ces événements historiques.



### 8. Commandes de consultation



Depuis PowerShell, à la racine du projet :



Afficher les dernières lignes des journaux :



```powershell

docker compose logs --tail=30 postgres

```



Rechercher les erreurs de permissions :



```powershell

docker compose logs postgres 2>\&1 | Select-String "permission denied"

```



Rechercher les événements de connexion :



```powershell

docker compose logs postgres 2>\&1 | Select-String "connection authorized"

```



Ces commandes consultent les journaux sans modifier les données.



### 9. Limites et améliorations possibles



Le dispositif actuel fournit un premier niveau de contrôle d'accès et de traçabilité.



Cependant :



- Les connexions applicatives utilisent encore un compte PostgreSQL partagé.

- La journalisation complète des requêtes SQL n'est pas activée.

- L'extension `pgAudit` n'est pas installée.

- La vue `streaming.audit\_transactions\_summary` fournit des statistiques agrégées et ne constitue pas un journal d'événements de sécurité.

- La politique de conservation, de rotation et de centralisation des journaux reste à formaliser.

- Les contrôles de santé Docker produisent régulièrement des événements de connexion, ce qui augmente le volume des journaux.



Les améliorations envisageables sont la création de comptes techniques distincts, le renforcement de l'audit SQL et la centralisation sécurisée des journaux.



### 10. Synthèse pour la soutenance E7



La sécurité du DataMarket repose sur deux mécanismes complémentaires :



\*\*Le RBAC\*\* contrôle les opérations autorisées selon les responsabilités des rôles PostgreSQL.



\*\*La journalisation\*\* permet de retrouver les événements de connexion, de déconnexion et les erreurs d'autorisation enregistrées par PostgreSQL.



Les résultats obtenus sont :



- Quatre rôles PostgreSQL créés.

- Dix-sept contrôles RBAC réussis.

- Quatre refus d'accès retrouvés dans les journaux historiques.

- Journalisation des connexions et déconnexions activée et vérifiée.

- Configuration reproductible documentée dans un script SQL.

- Scripts de sécurité versionnés sur GitHub.



Ces travaux contribuent aux objectifs de sécurisation, d'exploitation et de supervision du DataMarket.



### 11. Fichiers de référence



```text

sql/

└── security/

&#x20;   ├── 01\_rbac\_roles\_permissions.sql

&#x20;   ├── 02\_rbac\_tests.sql

&#x20;   ├── 03\_postgresql\_audit.sql

&#x20;   └── README.md

```



\*\*Branche Git :\*\* `rattrapage-e7`



\*\*Projet :\*\* Carrefour DataMarket — Rattrapage Bloc 4 / E7



