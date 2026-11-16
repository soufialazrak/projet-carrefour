-- ============================================================
-- CARREFOUR DATAMARKET - E7
-- Tests des droits de recherche dans le catalogue
-- Fichier : sql/catalogue/02_catalogue_tests.sql
-- Lecture seule.
--
-- docker exec -it datamarket_carrefour_pg psql -U soufia -d datamarket_carrefour -f /sql/catalogue/02_catalogue_tests.sql
-- ============================================================

-- Ce que voit chaque role (SET ROLE = on se met a sa place)
SET ROLE role_data_engineer;
SELECT COUNT(*) AS de_total FROM catalogue.objets \gset
RESET ROLE;

SET ROLE role_auditeur;
SELECT COUNT(*) AS aud_total FROM catalogue.objets \gset
RESET ROLE;

SET ROLE role_data_analyst;
SELECT COUNT(*) AS ana_total,
       COUNT(*) FILTER (WHERE lower(couche) = 'bronze') AS ana_bronze,
       COUNT(*) FILTER (WHERE chemin_objet ILIKE '%products%') AS ana_recherche
FROM catalogue.objets \gset
RESET ROLE;

SELECT COUNT(*) AS total_reel,
       COUNT(*) FILTER (WHERE lower(couche) IN ('silver','gold')) AS total_silver_gold
FROM catalogue.objets \gset

SELECT * FROM (VALUES
  ('Data Engineer', 'Recherche dans tout le catalogue',
     CASE WHEN :de_total = :total_reel THEN 'OK' ELSE 'ECHEC' END,
     :de_total || ' objets visibles'),
  ('Auditeur', 'Recherche dans tout le catalogue',
     CASE WHEN :aud_total = :total_reel THEN 'OK' ELSE 'ECHEC' END,
     :aud_total || ' objets visibles'),
  ('Data Analyst', 'Recherche limitee a Silver / Gold',
     CASE WHEN :ana_total = :total_silver_gold THEN 'OK' ELSE 'ECHEC' END,
     :ana_total || ' objets visibles'),
  ('Data Analyst', 'Objets Bronze invisibles',
     CASE WHEN :ana_bronze = 0 THEN 'OK' ELSE 'ECHEC' END,
     :ana_bronze || ' objet Bronze visible'),
  ('Data Analyst', 'Recherche par mot-cle "products"',
     CASE WHEN :ana_recherche > 0 THEN 'OK' ELSE 'ECHEC' END,
     :ana_recherche || ' resultat(s)'),
  ('Data Analyst', 'Modification du catalogue interdite',
     CASE WHEN NOT has_table_privilege('role_data_analyst','catalogue.objets','UPDATE') THEN 'OK' ELSE 'ECHEC' END,
     'UPDATE refuse'),
  ('Marketing', 'Acces au catalogue interdit',
     CASE WHEN NOT has_table_privilege('role_marketing','catalogue.objets','SELECT') THEN 'OK' ELSE 'ECHEC' END,
     'SELECT refuse')
) AS t(role, test, resultat, detail);
