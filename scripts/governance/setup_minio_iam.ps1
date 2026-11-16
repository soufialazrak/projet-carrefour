# =====================================================================
# setup_minio_iam.ps1 - Gouvernance des acces au Data Lake MinIO (C21)
# Projet PHENIX - Carrefour Data Market (E7)
#
# Cree 4 politiques, 4 groupes et 4 utilisateurs MinIO.
# Les droits sont attribues aux GROUPES, jamais directement aux utilisateurs.
#
# Lancement (depuis la racine du projet) :
#   .\scripts\governance\setup_minio_iam.ps1
# =====================================================================
$ErrorActionPreference = "Stop"
$Container = "phenix_minio"
$PolicyDir = Join-Path $PSScriptRoot "policies"

# --- 1. Lecture du fichier .env (aucun mot de passe dans le script) ---
$cfg = @{}
Get-Content ".env" | Where-Object { $_ -match "^\s*[^#].*=" } | ForEach-Object {
    $k, $v = $_ -split "=", 2
    $cfg[$k.Trim()] = $v.Trim()
}
foreach ($key in "MINIO_ROOT_USER","MINIO_ROOT_PASSWORD","MINIO_PWD_INGESTION",
                 "MINIO_PWD_DATA_ENGINEER","MINIO_PWD_ANALYST","MINIO_PWD_AUDITOR") {
    if (-not $cfg.ContainsKey($key)) { throw "Variable $key absente du fichier .env" }
}

function Invoke-Mc {
    docker exec $Container mc @args
    if ($LASTEXITCODE -ne 0) { throw "Echec de la commande : mc $args" }
}

Write-Host "`n=== 1. Verification du client mc dans le conteneur ===" -ForegroundColor Cyan
Invoke-Mc --version
Invoke-Mc alias set local http://localhost:9000 $cfg["MINIO_ROOT_USER"] $cfg["MINIO_ROOT_PASSWORD"]

Write-Host "`n=== 2. Creation des politiques d'acces ===" -ForegroundColor Cyan
docker exec $Container mkdir -p /tmp/policies | Out-Null
docker cp "$PolicyDir/." "${Container}:/tmp/policies"
$policies = "pol-ingestion","pol-data-engineer","pol-data-analyst","pol-auditor"
foreach ($p in $policies) { Invoke-Mc admin policy create local $p "/tmp/policies/$p.json" }

Write-Host "`n=== 3. Creation des utilisateurs ===" -ForegroundColor Cyan
$users = [ordered]@{
    "svc_ingestion" = @{ pwd = $cfg["MINIO_PWD_INGESTION"];     group = "grp-ingestion";      policy = "pol-ingestion" }
    "de_soufia"     = @{ pwd = $cfg["MINIO_PWD_DATA_ENGINEER"]; group = "grp-data-engineer";  policy = "pol-data-engineer" }
    "analyst_demo"  = @{ pwd = $cfg["MINIO_PWD_ANALYST"];       group = "grp-data-analyst";   policy = "pol-data-analyst" }
    "auditor_demo"  = @{ pwd = $cfg["MINIO_PWD_AUDITOR"];       group = "grp-auditor";        policy = "pol-auditor" }
}
foreach ($u in $users.Keys) { Invoke-Mc admin user add local $u $users[$u].pwd }

Write-Host "`n=== 4. Creation des groupes et attribution des politiques ===" -ForegroundColor Cyan
foreach ($u in $users.Keys) {
    $g = $users[$u].group
    Invoke-Mc admin group add local $g $u
    # Si la politique est deja attachee, MinIO renvoie une erreur sans gravite
    docker exec $Container mc admin policy attach local $users[$u].policy --group $g 2>$null
}

Write-Host "`n=== 5. Verification (capture pour le rapport) ===" -ForegroundColor Cyan
foreach ($g in "grp-ingestion","grp-data-engineer","grp-data-analyst","grp-auditor") {
    Invoke-Mc admin group info local $g
    Write-Host ""
}
Invoke-Mc admin user list local
Write-Host "`nGouvernance MinIO en place." -ForegroundColor Green
