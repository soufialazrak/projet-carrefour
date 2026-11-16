-- ============================================================
-- CARREFOUR DATAMARKET - E7
-- Catalogue de donnees dans PostgreSQL + droits de recherche
-- Fichier : sql/catalogue/01_catalogue_schema.sql
-- ============================================================
--
-- Charge catalogue_metier.csv (genere par enrichir_catalogue.py)
-- dans une table interrogeable, puis applique les droits d'acces
-- a l'INDEX (recherche dans le catalogue) :
--   - Data Engineer, Auditeur : tout le catalogue
--   - Data Analyst            : uniquement les objets Silver / Gold
--                               (Row Level Security)
--   - Marketing               : aucun acces
--
-- Prealable (PowerShell, racine du projet) :
--   docker cp catalogue\catalogue_metier.csv datamarket_carrefour_pg:/tmp/catalogue_metier.csv
-- Execution :
--   docker exec -it datamarket_carrefour_pg psql -U soufia -d datamarket_carrefour -f /sql/catalogue/01_catalogue_schema.sql
--
-- ATTENTION : la liste des colonnes du \copy doit correspondre
-- EXACTEMENT a l'en-tete de catalogue_metier.csv.
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS catalogue;

DROP TABLE IF EXISTS catalogue.objets;
CREATE TABLE catalogue.objets (
    id                       SERIAL PRIMARY KEY,
    couche                   TEXT NOT NULL,
    bucket                   TEXT NOT NULL,
    chemin_objet             TEXT NOT NULL,
    format                   TEXT,
    taille_octets            BIGINT,
    derniere_modification    TIMESTAMPTZ,
    uri_minio                TEXT,
    description_metier       TEXT,
    classification_proposee  TEXT,
    usage                    TEXT,
    charge_le                TIMESTAMP NOT NULL DEFAULT NOW()
);

\copy catalogue.objets(couche, bucket, chemin_objet, format, taille_octets, derniere_modification, uri_minio, description_metier, classification_proposee, usage) FROM '/tmp/catalogue_metier.csv' WITH (FORMAT csv, HEADER true, DELIMITER ';', ENCODING 'UTF8')

CREATE INDEX idx_catalogue_couche ON catalogue.objets(couche);

-- ------------------------------------------------------------
-- Droits d'acces a l'index du catalogue
-- ------------------------------------------------------------
GRANT USAGE ON SCHEMA catalogue TO role_data_engineer, role_data_analyst, role_auditeur;
GRANT SELECT ON catalogue.objets TO role_data_engineer, role_data_analyst, role_auditeur;
-- role_marketing : aucun GRANT -> aucun acces au catalogue

-- Filtrage par ligne : l'analyste ne voit pas les objets Bronze
ALTER TABLE catalogue.objets ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS p_catalogue_complet ON catalogue.objets;
CREATE POLICY p_catalogue_complet ON catalogue.objets
    FOR SELECT TO role_data_engineer, role_auditeur
    USING (true);

DROP POLICY IF EXISTS p_catalogue_analyste ON catalogue.objets;
CREATE POLICY p_catalogue_analyste ON catalogue.objets
    FOR SELECT TO role_data_analyst
    USING (lower(couche) IN ('silver', 'gold'));

COMMIT;

-- Controle du chargement
SELECT couche, COUNT(*) AS nb_objets, pg_size_pretty(SUM(taille_octets)) AS volume
FROM catalogue.objets
GROUP BY couche
ORDER BY couche;
