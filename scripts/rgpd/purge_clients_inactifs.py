"""
CARREFOUR DATAMARKET - E7
Procedure RGPD : anonymisation des clients inactifs depuis plus de 24 mois.

Remplace sql/rgpd/cleanup.sql (ses colonnes n'existaient pas dans la table).

Regle : un client sans activite (derniere transaction, derniere utilisation
de carte, creation du foyer) depuis plus de N mois voit ses donnees
personnelles effacees. customer_id est conserve (identifiant pseudonyme)
pour garder l'integrite des transactions ; la region est conservee
(donnee agregee, non identifiante).

Execute avec le compte svc_rgpd (droits limites aux colonnes personnelles).
Chaque passage est trace dans rgpd.journal_purge.

Usage (racine du projet) :
  python scripts/rgpd/purge_clients_inactifs.py                       # simulation
  python scripts/rgpd/purge_clients_inactifs.py --execution           # anonymisation
  python scripts/rgpd/purge_clients_inactifs.py --date-ref 2018-10-31 # donnees historiques
"""
import argparse
import os
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import psycopg2

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[2] / ".env")
except ImportError:
    pass


SQL_CANDIDATS = """
CREATE TEMP TABLE clients_inactifs ON COMMIT DROP AS
WITH derniere_activite AS (
    SELECT c.customer_id,
           GREATEST(MAX(t.transaction_timestamp),
                    MAX(lc.last_used_at),
                    MAX(h.household_created_at)) AS derniere_activite
    FROM datamarket.customers c
    JOIN datamarket.households h          ON h.household_id = c.household_id
    LEFT JOIN datamarket.loyalty_cards lc ON lc.customer_id = c.customer_id
    LEFT JOIN datamarket.transactions t   ON t.card_id = lc.card_id
    WHERE c.email_hash IS NOT NULL          -- pas encore anonymise
    GROUP BY c.customer_id
)
SELECT customer_id, derniere_activite
FROM derniere_activite
WHERE derniere_activite < %(date_ref)s::timestamp - make_interval(months => %(seuil)s);
"""

SQL_ANONYMISATION = """
UPDATE datamarket.customers c
SET first_name_encrypted = NULL,
    last_name_encrypted  = NULL,
    email_encrypted      = NULL,
    email_hash           = NULL,
    birth_year           = NULL,
    customer_city        = NULL,
    postal_code          = NULL
FROM clients_inactifs i
WHERE c.customer_id = i.customer_id;
"""

SQL_JOURNAL = """
INSERT INTO rgpd.journal_purge (mode, date_reference, seuil_mois, nb_identifies, nb_anonymises)
VALUES (%(mode)s, %(date_ref)s, %(seuil)s, %(nb_identifies)s, %(nb_anonymises)s);
"""


def url_connexion():
    """Compte svc_rgpd si defini, sinon DATABASE_URL. Adapte l'hote hors Docker."""
    url = os.environ.get("RGPD_DATABASE_URL") or os.environ["DATABASE_URL"]
    if os.environ.get("RUNNING_IN_DOCKER") == "1":
        return url
    parts = urlsplit(url)
    identifiants = parts.netloc.rsplit("@", 1)[0] + "@" if "@" in parts.netloc else ""
    return urlunsplit(parts._replace(netloc=identifiants + "localhost:5433"))


def main():
    parser = argparse.ArgumentParser(description="Purge RGPD des clients inactifs")
    parser.add_argument("--execution", action="store_true",
                        help="anonymise reellement (sinon : simulation)")
    parser.add_argument("--date-ref", default=None,
                        help="date de reference AAAA-MM-JJ (defaut : aujourd'hui)")
    parser.add_argument("--seuil-mois", type=int, default=24)
    args = parser.parse_args()

    mode = "execution" if args.execution else "simulation"
    date_ref = args.date_ref or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    params = {"date_ref": date_ref, "seuil": args.seuil_mois}

    connexion = psycopg2.connect(url_connexion(), connect_timeout=10)
    try:
        with connexion:
            with connexion.cursor() as cur:
                cur.execute(SQL_CANDIDATS, params)
                cur.execute("SELECT COUNT(*) FROM clients_inactifs")
                nb_identifies = cur.fetchone()[0]

                nb_anonymises = 0
                if args.execution:
                    cur.execute(SQL_ANONYMISATION)
                    nb_anonymises = cur.rowcount

                cur.execute(SQL_JOURNAL, {**params, "mode": mode,
                                          "nb_identifies": nb_identifies,
                                          "nb_anonymises": nb_anonymises})
                cur.execute("SELECT current_user")
                compte = cur.fetchone()[0]
    finally:
        connexion.close()

    print("=" * 60)
    print("PURGE RGPD - CLIENTS INACTIFS")
    print("=" * 60)
    print(f"Mode                    : {mode}")
    print(f"Compte PostgreSQL       : {compte}")
    print(f"Date de reference       : {date_ref[:10]}")
    print(f"Seuil d'inactivite      : {args.seuil_mois} mois")
    print(f"Clients identifies      : {nb_identifies}")
    print(f"Clients anonymises      : {nb_anonymises}")
    print("Trace enregistree dans  : rgpd.journal_purge")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
