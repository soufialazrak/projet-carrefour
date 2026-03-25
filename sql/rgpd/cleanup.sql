-- Script de gestion du cycle de vie des données clients (RGPD)
-- Anonymisation des données personnelles après 2 ans d'inactivité
UPDATE customers
SET 
    email = NULL,
    first_name = NULL,
    last_name = NULL
WHERE last_activity_date < NOW() - INTERVAL '2 years'
AND email IS NOT NULL;