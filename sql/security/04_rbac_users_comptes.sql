-- ============================================================
-- CARREFOUR DATAMARKET - E7
-- Comptes individuels, compte applicatif et role RGPD
-- Fichier : sql/security/04_rbac_users_comptes.sql
-- ============================================================
--
-- Complete 01_rbac_roles_permissions.sql :
--   1. Cree un role RGPD (droits limites a l'anonymisation).
--   2. Cree des comptes INDIVIDUELS (LOGIN) rattaches aux roles
--      collectifs : les droits sont portes par les groupes,
--      jamais par les individus.
--   3. Cree un compte applicatif dedie a l'API (lecture seule),
--      pour ne plus utiliser le super-utilisateur.
--
-- Aucun mot de passe n'est ecrit dans ce fichier : ils sont
-- transmis a l'execution avec l'option -v de psql :
--
-- docker exec -it datamarket_carrefour_pg psql -U soufia -d datamarket_carrefour ^
--   -v pwd_engineer=XXX -v pwd_analyst=XXX -v pwd_marketing=XXX ^
--   -v pwd_auditeur=XXX -v pwd_api=XXX -v pwd_rgpd=XXX ^
--   -f /sql/security/04_rbac_users_comptes.sql
-- ============================================================

BEGIN;

-- ------------------------------------------------------------
-- 1. ROLE COLLECTIF RGPD
-- Peut uniquement effacer les colonnes personnelles des clients
-- et ecrire dans le journal des purges.
-- ------------------------------------------------------------
SELECT 'CREATE ROLE role_rgpd NOLOGIN'
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'role_rgpd') \gexec

CREATE SCHEMA IF NOT EXISTS rgpd;

CREATE TABLE IF NOT EXISTS rgpd.journal_purge (
    id                SERIAL PRIMARY KEY,
    execute_le        TIMESTAMP NOT NULL DEFAULT NOW(),
    execute_par       TEXT      NOT NULL DEFAULT current_user,
    mode              TEXT      NOT NULL CHECK (mode IN ('simulation', 'execution')),
    date_reference    TIMESTAMP NOT NULL,
    seuil_mois        INT       NOT NULL,
    nb_identifies     INT       NOT NULL,
    nb_anonymises     INT       NOT NULL
);

GRANT USAGE ON SCHEMA datamarket TO role_rgpd;
GRANT SELECT ON datamarket.customers, datamarket.loyalty_cards,
                datamarket.transactions, datamarket.households TO role_rgpd;
GRANT UPDATE (first_name_encrypted, last_name_encrypted, email_encrypted,
              email_hash, birth_year, customer_city, postal_code)
      ON datamarket.customers TO role_rgpd;
GRANT USAGE ON SCHEMA rgpd TO role_rgpd;
GRANT SELECT, INSERT ON rgpd.journal_purge TO role_rgpd;
GRANT USAGE ON SEQUENCE rgpd.journal_purge_id_seq TO role_rgpd;
-- L'auditeur peut consulter le journal des purges (preuve de conformite)
GRANT USAGE ON SCHEMA rgpd TO role_auditeur;
GRANT SELECT ON rgpd.journal_purge TO role_auditeur;

-- ------------------------------------------------------------
-- 2. ROLE APPLICATIF API (lecture seule)
-- ------------------------------------------------------------
SELECT 'CREATE ROLE role_app_api NOLOGIN'
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'role_app_api') \gexec

GRANT USAGE ON SCHEMA gold, datamarket TO role_app_api;
GRANT SELECT ON ALL TABLES IN SCHEMA gold TO role_app_api;
-- L'API restitue les fiches clients (dechiffrement applicatif) :
-- lecture seule, aucune ecriture possible.
GRANT SELECT ON ALL TABLES IN SCHEMA datamarket TO role_app_api;

-- ------------------------------------------------------------
-- 3. COMPTES INDIVIDUELS (LOGIN) RATTACHES AUX GROUPES
-- Aucun GRANT n'est fait directement a un compte individuel.
-- ------------------------------------------------------------
SELECT format('CREATE ROLE %I LOGIN', u)
FROM unnest(ARRAY['u_soufia_engineer','u_analyst_demo','u_marketing_demo',
                  'u_auditeur_demo','svc_api','svc_rgpd']) AS u
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = u) \gexec

ALTER ROLE u_soufia_engineer PASSWORD :'pwd_engineer';
ALTER ROLE u_analyst_demo    PASSWORD :'pwd_analyst';
ALTER ROLE u_marketing_demo  PASSWORD :'pwd_marketing';
ALTER ROLE u_auditeur_demo   PASSWORD :'pwd_auditeur';
ALTER ROLE svc_api           PASSWORD :'pwd_api';
ALTER ROLE svc_rgpd          PASSWORD :'pwd_rgpd';

GRANT role_data_engineer TO u_soufia_engineer;
GRANT role_data_analyst  TO u_analyst_demo;
GRANT role_marketing     TO u_marketing_demo;
GRANT role_auditeur      TO u_auditeur_demo;
GRANT role_app_api       TO svc_api;
GRANT role_rgpd          TO svc_rgpd;

COMMIT;

-- ------------------------------------------------------------
-- 4. VERIFICATION : qui appartient a quel groupe (capture rapport)
-- ------------------------------------------------------------
SELECT
    m.rolname                         AS compte_individuel,
    r.rolname                         AS role_collectif,
    m.rolcanlogin                     AS peut_se_connecter,
    r.rolcanlogin                     AS role_groupe_login
FROM pg_auth_members am
JOIN pg_roles r ON r.oid = am.roleid
JOIN pg_roles m ON m.oid = am.member
WHERE r.rolname LIKE 'role\_%'
ORDER BY r.rolname, m.rolname;
