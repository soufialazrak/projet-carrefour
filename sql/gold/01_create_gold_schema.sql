- =========================
-- CREATE GOLD SCHEMA
-- =========================

CREATE SCHEMA IF NOT EXISTS gold;

COMMENT ON SCHEMA gold IS
'Couche Gold : vues analytiques et segmentation marketing construites à partir de la couche Silver.';