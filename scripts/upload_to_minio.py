
import os
from pathlib import Path

from dotenv import load_dotenv
from minio import Minio

# Racine du projet PHENIX
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Charger les identifiants depuis .env
load_dotenv(PROJECT_ROOT / ".env")

# Connexion au serveur MinIO local
client = Minio(
    "localhost:9000",
    access_key=os.environ["MINIO_ROOT_USER"],
    secret_key=os.environ["MINIO_ROOT_PASSWORD"],
    secure=False,
)

# Fichier fictif utilisé pour le premier test
file_path = PROJECT_ROOT / "data" / "tests" / "categories_test.csv"

bucket_name = "phenix-bronze"
object_name = "tests/categories_test.csv"

if not file_path.is_file():
    raise FileNotFoundError(f"Fichier introuvable : {file_path}")

if not client.bucket_exists(bucket_name):
    raise RuntimeError(f"Bucket introuvable : {bucket_name}")

# Envoyer le fichier dans le Data Lake
result = client.fput_object(
    bucket_name,
    object_name,
    str(file_path),
    content_type="text/csv",
)

print("Ingestion réussie !")
print(f"Bucket : {bucket_name}")
print(f"Objet : {object_name}")
print(f"ETag : {result.etag}")
