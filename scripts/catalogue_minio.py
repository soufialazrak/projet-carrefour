
import csv
import os
from pathlib import Path

from dotenv import load_dotenv
from minio import Minio

PROJECT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_DIR / ".env")

BUCKETS = ["phenix-bronze", "phenix-silver"]
OUTPUT = PROJECT_DIR / "catalogue" / "catalogue_minio.csv"


def main():
    client = Minio(
        "localhost:9000",
        access_key=os.environ["MINIO_ROOT_USER"],
        secret_key=os.environ["MINIO_ROOT_PASSWORD"],
        secure=False,
    )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    lignes = []

    for bucket in BUCKETS:
        if not client.bucket_exists(bucket):
            print(f"Bucket absent : {bucket}")
            continue

        for obj in client.list_objects(bucket, recursive=True):
            if obj.is_dir:
                continue

            extension = Path(obj.object_name).suffix.lower()
            couche = "Bronze" if bucket == "phenix-bronze" else "Silver"

            lignes.append({
                "couche": couche,
                "bucket": bucket,
                "chemin_objet": obj.object_name,
                "format": extension.lstrip(".") or "inconnu",
                "taille_octets": obj.size,
                "derniere_modification": (
                    obj.last_modified.isoformat()
                    if obj.last_modified else ""
                ),
                "uri_minio": f"s3://{bucket}/{obj.object_name}",
            })

    champs = [
        "couche",
        "bucket",
        "chemin_objet",
        "format",
        "taille_octets",
        "derniere_modification",
        "uri_minio",
    ]

    with OUTPUT.open("w", newline="", encoding="utf-8-sig") as fichier:
        writer = csv.DictWriter(fichier, fieldnames=champs, delimiter=";")
        writer.writeheader()
        writer.writerows(sorted(
            lignes,
            key=lambda x: (x["bucket"], x["chemin_objet"])
        ))

    print(f"Catalogue généré : {OUTPUT}")
    print(f"Nombre d'objets recensés : {len(lignes)}")


if __name__ == "__main__":
    main()
