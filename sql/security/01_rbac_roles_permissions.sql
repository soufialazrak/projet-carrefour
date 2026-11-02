
-- ============================================================
-- CARREFOUR DATAMARKET - E7
-- Gestion des habilitations PostgreSQL (RBAC)
-- Fichier : sql/security/01_rbac_roles_permissions.sql
-- ============================================================
--
-- Objectif :
-- Appliquer le principe du moindre privilege.
--
-- Ce script :
--   1. Cree les quatre roles collectifs si necessaire.
--   2. Cree deux vues agregees pour Marketing et Audit.
--   3. Attribue les autorisations minimales.
--
-- Aucun compte utilisateur n'est cree.
-- Aucune donnee historique n'est modifiee.
-- Aucun droit n'est retire aux comptes existants.
--
-- Prerequis : schemas gold et streaming et leurs
-- tables/vues sources deja presents.
-- Execution avec un compte administrateur PostgreSQL.
-- ============================================================

BEGIN;

-- ============================================================
-- 1. CREATION DES ROLES COLLECTIFS
-- ============================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_roles
        WHERE rolname = 'role_data_engineer'
    ) THEN
        CREATE ROLE role_data_engineer NOLOGIN;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_roles
        WHERE rolname = 'role_data_analyst'
    ) THEN
        CREATE ROLE role_data_analyst NOLOGIN;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_roles
        WHERE rolname = 'role_marketing'
    ) THEN
        CREATE ROLE role_marketing NOLOGIN;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_roles
        WHERE rolname = 'role_auditeur'
    ) THEN
        CREATE ROLE role_auditeur NOLOGIN;
    END IF;
END
$$;

-- ============================================================
-- 2. VUE AGREGEE POUR LE MARKETING
-- ============================================================

CREATE OR REPLACE VIEW gold.marketing_segments_summary AS
SELECT
    macro_segment,
    COUNT(*) AS nombre_foyers,
    ROUND(
        100.0 * COUNT(*) / SUM(COUNT(*)) OVER (),
        2
    ) AS pourcentage
FROM gold.household_rfm_segments_e7
GROUP BY macro_segment;

-- ============================================================
-- 3. VUE DE CONTROLE POUR L'AUDITEUR
-- ============================================================

CREATE OR REPLACE VIEW streaming.audit_transactions_summary AS
SELECT
    COUNT(*) AS nombre_transactions,
    COUNT(DISTINCT event_id) AS identifiants_uniques,
    COALESCE(SUM(amount), 0) AS montant_total
FROM streaming.transactions_e7;

-- ============================================================
-- 4. ROLE DATA ANALYST
-- Lecture des vues analytiques Gold.
-- Aucun acces direct aux tables datamarket.
-- ============================================================

GRANT USAGE ON SCHEMA gold
TO role_data_analyst;

GRANT SELECT ON ALL TABLES IN SCHEMA gold
TO role_data_analyst;

-- ============================================================
-- 5. ROLE MARKETING
-- Lecture de la synthese agregee uniquement.
-- ============================================================

GRANT USAGE ON SCHEMA gold
TO role_marketing;

GRANT SELECT ON gold.marketing_segments_summary
TO role_marketing;

-- ============================================================
-- 6. ROLE DATA ENGINEER
-- Lecture et insertion des transactions streaming.
-- Pas de droits UPDATE ou DELETE.
-- ============================================================

GRANT USAGE ON SCHEMA streaming
TO role_data_engineer;

GRANT SELECT, INSERT ON streaming.transactions_e7
TO role_data_engineer;

-- ============================================================
-- 7. ROLE AUDITEUR
-- Lecture de la synthese de controle uniquement.
-- ============================================================

GRANT USAGE ON SCHEMA streaming
TO role_auditeur;

GRANT SELECT ON streaming.audit_transactions_summary
TO role_auditeur;

COMMIT;

-- ============================================================
-- FIN DU SCRIPT RBAC
-- ============================================================
