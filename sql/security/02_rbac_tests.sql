
-- ============================================================
-- CARREFOUR DATAMARKET - E7
-- Tests de securite PostgreSQL (RBAC)
-- Fichier : sql/security/02_rbac_tests.sql
-- ============================================================
--
-- Objectif :
-- Verifier les droits des quatre roles collectifs.
--
-- Resultat attendu :
-- Tous les tests doivent afficher OK.
--
-- Ce script est en lecture seule.
-- ============================================================

-- ============================================================
-- 1. VERIFICATION DES QUATRE ROLES
-- ============================================================

SELECT
    rolname AS role,
    CASE
        WHEN rolcanlogin = FALSE THEN 'OK'
        ELSE 'ECHEC'
    END AS resultat
FROM pg_roles
WHERE rolname IN (
    'role_data_engineer',
    'role_data_analyst',
    'role_marketing',
    'role_auditeur'
)
ORDER BY rolname;

-- ============================================================
-- 2. ROLE DATA ANALYST
-- ============================================================

SELECT
    'Data Analyst - Lecture RFM' AS test,
    CASE
        WHEN has_table_privilege(
            'role_data_analyst',
            'gold.household_rfm_segments_e7',
            'SELECT'
        )
        THEN 'OK'
        ELSE 'ECHEC'
    END AS resultat

UNION ALL

SELECT
    'Data Analyst - Modification RFM interdite',
    CASE
        WHEN NOT has_table_privilege(
            'role_data_analyst',
            'gold.household_rfm_segments_e7',
            'UPDATE'
        )
        THEN 'OK'
        ELSE 'ECHEC'
    END

UNION ALL

SELECT
    'Data Analyst - Schema clients interdit',
    CASE
        WHEN NOT has_schema_privilege(
            'role_data_analyst',
            'datamarket',
            'USAGE'
        )
        THEN 'OK'
        ELSE 'ECHEC'
    END;

-- ============================================================
-- 3. ROLE MARKETING
-- ============================================================

SELECT
    'Marketing - Lecture synthese autorisee' AS test,
    CASE
        WHEN has_table_privilege(
            'role_marketing',
            'gold.marketing_segments_summary',
            'SELECT'
        )
        THEN 'OK'
        ELSE 'ECHEC'
    END AS resultat

UNION ALL

SELECT
    'Marketing - Segmentation clients interdite',
    CASE
        WHEN NOT has_table_privilege(
            'role_marketing',
            'gold.customer_segmentation',
            'SELECT'
        )
        THEN 'OK'
        ELSE 'ECHEC'
    END

UNION ALL

SELECT
    'Marketing - Schema clients interdit',
    CASE
        WHEN NOT has_schema_privilege(
            'role_marketing',
            'datamarket',
            'USAGE'
        )
        THEN 'OK'
        ELSE 'ECHEC'
    END;

-- ============================================================
-- 4. ROLE DATA ENGINEER
-- ============================================================

SELECT
    'Data Engineer - Lecture streaming' AS test,
    CASE
        WHEN has_table_privilege(
            'role_data_engineer',
            'streaming.transactions_e7',
            'SELECT'
        )
        THEN 'OK'
        ELSE 'ECHEC'
    END AS resultat

UNION ALL

SELECT
    'Data Engineer - Insertion streaming',
    CASE
        WHEN has_table_privilege(
            'role_data_engineer',
            'streaming.transactions_e7',
            'INSERT'
        )
        THEN 'OK'
        ELSE 'ECHEC'
    END

UNION ALL

SELECT
    'Data Engineer - Modification interdite',
    CASE
        WHEN NOT has_table_privilege(
            'role_data_engineer',
            'streaming.transactions_e7',
            'UPDATE'
        )
        THEN 'OK'
        ELSE 'ECHEC'
    END

UNION ALL

SELECT
    'Data Engineer - Suppression interdite',
    CASE
        WHEN NOT has_table_privilege(
            'role_data_engineer',
            'streaming.transactions_e7',
            'DELETE'
        )
        THEN 'OK'
        ELSE 'ECHEC'
    END;

-- ============================================================
-- 5. ROLE AUDITEUR
-- ============================================================

SELECT
    'Auditeur - Lecture synthese autorisee' AS test,
    CASE
        WHEN has_table_privilege(
            'role_auditeur',
            'streaming.audit_transactions_summary',
            'SELECT'
        )
        THEN 'OK'
        ELSE 'ECHEC'
    END AS resultat

UNION ALL

SELECT
    'Auditeur - Transactions interdites',
    CASE
        WHEN NOT has_table_privilege(
            'role_auditeur',
            'streaming.transactions_e7',
            'SELECT'
        )
        THEN 'OK'
        ELSE 'ECHEC'
    END

UNION ALL

SELECT
    'Auditeur - Modification interdite',
    CASE
        WHEN NOT has_table_privilege(
            'role_auditeur',
            'streaming.transactions_e7',
            'UPDATE'
        )
        THEN 'OK'
        ELSE 'ECHEC'
    END;

-- ============================================================
-- FIN DES TESTS RBAC
-- ============================================================
