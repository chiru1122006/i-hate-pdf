# Azure Deployment Pre-flight Check
# Verifies all prerequisites before deployment

Write-Host "`n╔════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  Word to PDF - Azure Pre-flight Check ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════╝`n" -ForegroundColor Cyan

$allGood = $true

# Check 1: Azure CLI
Write-Host "Checking Azure CLI..." -NoNewline
if (Get-Command az -ErrorAction SilentlyContinue) {
    $azVersion = (az version --query '"azure-cli"' -o tsv 2>$null)
    Write-Host " ✅ Installed (v$azVersion)" -ForegroundColor Green
} else {
    Write-Host " ❌ Not installed" -ForegroundColor Red
    Write-Host "   Install from: https://aka.ms/installazurecliwindows" -ForegroundColor Yellow
    $allGood = $false
}

# Check 2: Azure Login Status
Write-Host "Checking Azure login..." -NoNewline
$account = az account show 2>$null | ConvertFrom-Json
if ($account) {
    Write-Host " ✅ Logged in as $($account.user.name)" -ForegroundColor Green
} else {
    Write-Host " ⚠️  Not logged in" -ForegroundColor Yellow
    Write-Host "   Run: az login" -ForegroundColor Yellow
}

# Check 3: Python
Write-Host "Checking Python..." -NoNewline
if (Get-Command python -ErrorAction SilentlyContinue) {
    $pyVersion = (python --version 2>&1)
    Write-Host " ✅ $pyVersion" -ForegroundColor Green
} else {
    Write-Host " ⚠️  Not installed (optional for local testing)" -ForegroundColor Yellow
}

# Check 4: Git
Write-Host "Checking Git..." -NoNewline
if (Get-Command git -ErrorAction SilentlyContinue) {
    $gitVersion = (git --version)
    Write-Host " ✅ $gitVersion" -ForegroundColor Green
} else {
    Write-Host " ⚠️  Not installed (optional for CI/CD)" -ForegroundColor Yellow
}

# Check 5: Docker
Write-Host "Checking Docker..." -NoNewline
if (Get-Command docker -ErrorAction SilentlyContinue) {
    $dockerVersion = (docker --version)
    Write-Host " ✅ $dockerVersion" -ForegroundColor Green
} else {
    Write-Host " ⚠️  Not installed (optional for local testing)" -ForegroundColor Yellow
}

# Check 6: Project Files
Write-Host "Checking project files..." -NoNewline
$requiredFiles = @("app\main.py", "requirements.txt", "Dockerfile.azure", "static\index.html")
$missingFiles = @()
foreach ($file in $requiredFiles) {
    if (-not (Test-Path $file)) {
        $missingFiles += $file
    }
}
if ($missingFiles.Count -eq 0) {
    Write-Host " ✅ All files present" -ForegroundColor Green
} else {
    Write-Host " ❌ Missing files" -ForegroundColor Red
    foreach ($file in $missingFiles) {
        Write-Host "   - $file" -ForegroundColor Red
    }
    $allGood = $false
}

# Check 7: Azure Subscription
Write-Host "Checking Azure subscription..." -NoNewline
if ($account) {
    $subscription = az account show --query name -o tsv 2>$null
    Write-Host " ✅ $subscription" -ForegroundColor Green
} else {
    Write-Host " ⚠️  Please login first" -ForegroundColor Yellow
}

Write-Host "`n" -NoNewline

# Summary
if ($allGood) {
    Write-Host "╔════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║  ✅ Ready for deployment!          ║" -ForegroundColor Green
    Write-Host "╚════════════════════════════════════╝" -ForegroundColor Green
    Write-Host "`nNext steps:" -ForegroundColor Cyan
    Write-Host "  1. Run: .\quick-deploy-azure.ps1" -ForegroundColor White
    Write-Host "  2. Or follow AZURE_QUICKSTART.md for Docker deployment`n" -ForegroundColor White
} else {
    Write-Host "╔════════════════════════════════════╗" -ForegroundColor Red
    Write-Host "║  ❌ Prerequisites missing          ║" -ForegroundColor Red
    Write-Host "╚════════════════════════════════════╝" -ForegroundColor Red
    Write-Host "`nPlease install missing components above.`n" -ForegroundColor Yellow
}

# Deployment options
Write-Host "─────────────────────────────────────" -ForegroundColor Gray
Write-Host "📚 Available Guides:" -ForegroundColor Cyan
Write-Host "  • AZURE_README.md       - Overview & quick start" -ForegroundColor White
Write-Host "  • AZURE_QUICKSTART.md   - Quick reference commands" -ForegroundColor White
Write-Host "  • AZURE_DEPLOYMENT.md   - Complete deployment guide" -ForegroundColor White
Write-Host "─────────────────────────────────────`n" -ForegroundColor Gray
