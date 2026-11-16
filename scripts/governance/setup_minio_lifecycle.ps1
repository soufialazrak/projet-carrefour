# =====================================================================
# setup_minio_lifecycle.ps1 - Cycle de vie automatique du Data Lake (C20)
# Regles ILM MinIO : suppression automatique selon la duree de retention.
# MinIO applique ces regles lui-meme, en tache de fond (scanner ILM).
#
# Lancement (depuis la racine du projet) :
#   .\scripts\governance\setup_minio_lifecycle.ps1
# =====================================================================
$ErrorActionPreference = "Stop"
$Container = "phenix_minio"

$cfg = @{}
Get-Content ".env" | Where-Object { $_ -match "^\s*[^#].*=" } | ForEach-Object {
    $k, $v = $_ -split "=", 2
    $cfg[$k.Trim()] = $v.Trim()
}
function Invoke-Mc {
    docker exec $Container mc @args
    if ($LASTEXITCODE -ne 0) { throw "Echec de la commande : mc $args" }
}
Invoke-Mc alias set local http://localhost:9000 $cfg["MINIO_ROOT_USER"] $cfg["MINIO_ROOT_PASSWORD"]

# Remise a zero pour que le script soit rejouable sans creer de doublons
$ErrorActionPreference = "Continue"
docker exec $Container mc ilm rule rm --all --force local/phenix-bronze 2>&1 | Out-Null
docker exec $Container mc ilm rule rm --all --force local/phenix-silver 2>&1 | Out-Null
$ErrorActionPreference = "Stop"

Write-Host "`n=== Creation des regles de cycle de vie ===" -ForegroundColor Cyan
# Bronze streaming : evenements bruts rejouables depuis Redpanda -> 30 jours
Invoke-Mc ilm rule add local/phenix-bronze --prefix "streaming/" --expire-days 30
# Bronze tests : fichiers techniques temporaires -> 7 jours
Invoke-Mc ilm rule add local/phenix-bronze --prefix "tests/" --expire-days 7
# Silver streaming : evenements valides, deja charges dans PostgreSQL -> 90 jours
Invoke-Mc ilm rule add local/phenix-silver --prefix "streaming/" --expire-days 90
# Silver tests -> 7 jours
Invoke-Mc ilm rule add local/phenix-silver --prefix "tests/" --expire-days 7
# NB : bronze/carrefour/ (CSV historiques = source de reference) n'expire pas
#      automatiquement ; sa purge suit la procedure RGPD (validation humaine).

Write-Host "`n=== Regles actives (capture pour le rapport) ===" -ForegroundColor Cyan
Invoke-Mc ilm rule ls local/phenix-bronze
Invoke-Mc ilm rule ls local/phenix-silver
