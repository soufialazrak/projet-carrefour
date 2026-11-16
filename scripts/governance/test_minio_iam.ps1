# =====================================================================
# test_minio_iam.ps1 - Tests des droits d'acces au Data Lake MinIO (C21)
# Verifie les 3 types de droits demandes par le referentiel E7 :
#   - ALIMENTATION  (s3:PutObject)
#   - INDEX / RECHERCHE (s3:ListBucket)
#   - RECUPERATION  (s3:GetObject)
#
# Lancement (depuis la racine du projet, apres setup_minio_iam.ps1) :
#   .\scripts\governance\test_minio_iam.ps1
# =====================================================================
$ErrorActionPreference = "Continue"
$Container = "phenix_minio"

$cfg = @{}
Get-Content ".env" | Where-Object { $_ -match "^\s*[^#].*=" } | ForEach-Object {
    $k, $v = $_ -split "=", 2
    $cfg[$k.Trim()] = $v.Trim()
}

# Un alias mc par utilisateur (connexion avec SES identifiants, pas root)
$null = docker exec $Container mc alias set ing http://localhost:9000 svc_ingestion $cfg["MINIO_PWD_INGESTION"] 2>&1
$null = docker exec $Container mc alias set de  http://localhost:9000 de_soufia     $cfg["MINIO_PWD_DATA_ENGINEER"] 2>&1
$null = docker exec $Container mc alias set ana http://localhost:9000 analyst_demo  $cfg["MINIO_PWD_ANALYST"] 2>&1
$null = docker exec $Container mc alias set aud http://localhost:9000 auditor_demo  $cfg["MINIO_PWD_AUDITOR"] 2>&1
$null = docker exec $Container sh -c "echo test_gouvernance > /tmp/iam_test.txt" 2>&1

$script:results = @()
function Test-Droit {
    param([string]$Role, [string]$Type, [string]$Test, [string]$Attendu, [string[]]$McArgs)
    $null = docker exec $Container mc @McArgs 2>&1
    $obtenu = if ($LASTEXITCODE -eq 0) { "Autorise" } else { "Refuse" }
    $statut = if ($obtenu -eq $Attendu) { "OK" } else { "ECHEC" }
    $script:results += [pscustomobject]@{
        Role = $Role; Droit = $Type; Test = $Test; Attendu = $Attendu; Obtenu = $obtenu; Resultat = $statut
    }
}

$BRZ = "phenix-bronze/carrefour/carrefour_products.csv"
$SLV = "phenix-silver/e7/products.csv"
$PII = "phenix-silver/e7/customers.csv"

# --- Compte de service d'ingestion ---
Test-Droit "Ingestion" "Alimentation" "Ecriture dans Bronze"         "Autorise" @("cp","/tmp/iam_test.txt","ing/phenix-bronze/tests/iam_test.txt")
Test-Droit "Ingestion" "Alimentation" "Ecriture dans Silver"         "Refuse"   @("cp","/tmp/iam_test.txt","ing/phenix-silver/tests/iam_test.txt")
Test-Droit "Ingestion" "Recuperation" "Lecture d'un fichier Bronze"  "Refuse"   @("stat","ing/$BRZ")
# --- Data Engineer ---
Test-Droit "Data Engineer" "Alimentation" "Ecriture dans Silver"     "Autorise" @("cp","/tmp/iam_test.txt","de/phenix-silver/tests/iam_test.txt")
Test-Droit "Data Engineer" "Recuperation" "Lecture d'un fichier Bronze" "Autorise" @("stat","de/$BRZ")
Test-Droit "Data Engineer" "Index"        "Recherche dans Bronze"    "Autorise" @("ls","de/phenix-bronze/carrefour/")
# --- Data Analyst ---
Test-Droit "Data Analyst" "Index"        "Recherche dans Silver"     "Autorise" @("ls","ana/phenix-silver/e7/")
Test-Droit "Data Analyst" "Recuperation" "Lecture produits Silver"   "Autorise" @("stat","ana/$SLV")
Test-Droit "Data Analyst" "Recuperation" "Lecture clients (RGPD)"    "Refuse"   @("stat","ana/$PII")
Test-Droit "Data Analyst" "Index"        "Recherche dans Bronze"     "Refuse"   @("ls","ana/phenix-bronze/")
Test-Droit "Data Analyst" "Alimentation" "Ecriture dans Silver"      "Refuse"   @("cp","/tmp/iam_test.txt","ana/phenix-silver/tests/iam_test.txt")
# --- Auditeur ---
Test-Droit "Auditeur" "Index"        "Recherche dans Bronze"         "Autorise" @("ls","aud/phenix-bronze/carrefour/")
Test-Droit "Auditeur" "Recuperation" "Lecture d'un fichier Bronze"   "Refuse"   @("stat","aud/$BRZ")
Test-Droit "Auditeur" "Alimentation" "Ecriture dans Bronze"          "Refuse"   @("cp","/tmp/iam_test.txt","aud/phenix-bronze/tests/iam_test.txt")

# Nettoyage des fichiers de test (par le Data Engineer, seul autorise a supprimer)
$null = docker exec $Container mc rm de/phenix-bronze/tests/iam_test.txt 2>&1
$null = docker exec $Container mc rm de/phenix-silver/tests/iam_test.txt 2>&1

Write-Host "`n=== TESTS DES DROITS D'ACCES AU DATA LAKE MINIO ===" -ForegroundColor Cyan
$script:results | Format-Table -AutoSize
$nbOk = ($script:results | Where-Object { $_.Resultat -eq "OK" }).Count
Write-Host "Tests reussis : $nbOk / $($script:results.Count)" -ForegroundColor Green

New-Item -ItemType Directory -Force -Path "catalogue" | Out-Null
$script:results | Export-Csv "catalogue\tests_droits_minio.csv" -NoTypeInformation -Delimiter ";" -Encoding UTF8
Write-Host "Resultats exportes : catalogue\tests_droits_minio.csv"
