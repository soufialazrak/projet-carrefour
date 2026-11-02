
-- ============================================================
-- CARREFOUR DATAMARKET - E7
-- Configuration de la journalisation PostgreSQL
-- Fichier : sql/security/03_postgresql_audit.sql
-- ============================================================
--
-- OBJECTIF
-- Tracer les connexions et deconnexions PostgreSQL
-- pour faciliter la supervision et l'analyse des incidents.
--
-- PRECAUTIONS
-- Executer avec un compte administrateur PostgreSQL.
-- Executer avec psql, sans --single-transaction.
-- ALTER SYSTEM doit etre execute hors transaction.
-- Aucun changement des donnees metier.
--
-- ============================================================

-- 1. Identifier l'utilisateur, la base et l'application
-- dans les messages de journalisation.

ALTER SYSTEM SET log_line_prefix =
    '%m [%p] user=%u db=%d app=%a ';

-- 2. Journaliser les connexions.

ALTER SYSTEM SET log_connections = on;

-- 3. Journaliser les deconnexions.

ALTER SYSTEM SET log_disconnections = on;

-- 4. Conserver les journaux sur stderr.
-- Docker peut ainsi les recuperer.

ALTER SYSTEM SET log_destination = 'stderr';

-- 5. Recharger la configuration sans redemarrage.

SELECT pg_reload_conf();

-- 6. Verifier les parametres actifs.

SELECT
    name,
    setting
FROM pg_settings
WHERE name IN (
    'log_destination',
    'log_line_prefix',
    'log_connections',
    'log_disconnections'
)
ORDER BY name;

-- ============================================================
-- CONSULTATION DES JOURNAUX
-- ============================================================
--
-- Depuis PowerShell, a la racine du projet :
--
-- docker compose logs --tail=30 postgres
--
-- Evenements recherches :
-- connection received
-- connection authorized
-- disconnection
-- ERROR: permission denied
--
-- ============================================================
-- LIMITES
-- ============================================================
--
-- Cette configuration ne journalise pas toutes les
-- requetes SQL executees.
--
-- Elle ne remplace pas un systeme d'audit complet
-- comme pgAudit.
--
-- Les applications utilisant un compte PostgreSQL
-- partage ne sont pas identifiables individuellement
-- par le seul nom d'utilisateur.
--
-- Les journaux peuvent contenir des informations
-- sensibles. Leur acces doit etre restreint.
--
-- ============================================================
-- FIN DU SCRIPT
-- ============================================================
