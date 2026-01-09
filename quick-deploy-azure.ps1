# Quick Start - Azure Deployment
# Simple one-command deployment to Azure

Write-Host "================================" -ForegroundColor Cyan
Write-Host "Word to PDF - Azure Quick Deploy" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check Azure CLI
if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Azure CLI not found!" -ForegroundColor Red
    Write-Host "📥 Install from: https://aka.ms/installazurecliwindows" -ForegroundColor Yellow
    Write-Host ""
    $install = Read-Host "Open installation page? (y/n)"
    if ($install -eq "y") {
        Start-Process "https://aka.ms/installazurecliwindows"
    }
    exit 1
}

Write-Host "✅ Azure CLI found" -ForegroundColor Green
Write-Host ""

# Get user inputs
Write-Host "📝 Configuration" -ForegroundColor Cyan
Write-Host "================`n" -ForegroundColor Cyan

$appName = Read-Host "Enter your app name (e.g., mywordtopdf)"
$appName = $appName.ToLower() -replace '[^a-z0-9-]', ''

$location = Read-Host "Enter Azure region (default: eastus)"
if ([string]::IsNullOrWhiteSpace($location)) {
    $location = "eastus"
}

Write-Host "`nSelect pricing tier:" -ForegroundColor Yellow
Write-Host "  1. F1  - Free (Limited, good for testing)" -ForegroundColor White
Write-Host "  2. B1  - Basic $13/month (Recommended)" -ForegroundColor Green
Write-Host "  3. B2  - Basic $26/month (Better performance)" -ForegroundColor White
Write-Host "  4. P1V2 - Premium $73/month (Production)" -ForegroundColor White

$tierChoice = Read-Host "`nEnter choice (1-4, default: 2)"
$sku = switch ($tierChoice) {
    "1" { "F1" }
    "3" { "B2" }
    "4" { "P1V2" }
    default { "B1" }
}

$resourceGroup = "$appName-rg"

Write-Host "`n📋 Deployment Summary" -ForegroundColor Cyan
Write-Host "===================" -ForegroundColor Cyan
Write-Host "App Name:       $appName" -ForegroundColor White
Write-Host "Resource Group: $resourceGroup" -ForegroundColor White
Write-Host "Region:         $location" -ForegroundColor White
Write-Host "Pricing Tier:   $sku" -ForegroundColor White
Write-Host ""

$confirm = Read-Host "Proceed with deployment? (y/n)"
if ($confirm -ne "y") {
    Write-Host "Deployment cancelled." -ForegroundColor Yellow
    exit 0
}

Write-Host "`n🚀 Starting deployment..." -ForegroundColor Green
Write-Host ""

try {
    # Run deployment script
    & ".\deploy-azure.ps1" -ResourceGroup $resourceGroup -AppName $appName -Location $location -Sku $sku
    
    Write-Host "`n✅ Deployment Complete!" -ForegroundColor Green
    Write-Host ""
    Write-Host "🌐 Your app will be available at:" -ForegroundColor Cyan
    Write-Host "   https://$appName.azurewebsites.net" -ForegroundColor White
    Write-Host ""
    Write-Host "📊 Manage your app:" -ForegroundColor Cyan
    Write-Host "   https://portal.azure.com" -ForegroundColor White
    Write-Host ""
    Write-Host "📖 Next steps:" -ForegroundColor Yellow
    Write-Host "   1. Deploy your code using Git (see instructions above)" -ForegroundColor White
    Write-Host "   2. Or use Docker deployment (see AZURE_DEPLOYMENT.md)" -ForegroundColor White
    Write-Host ""
    
} catch {
    Write-Host "`n❌ Deployment failed!" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host "`nCheck AZURE_DEPLOYMENT.md for troubleshooting" -ForegroundColor Yellow
}
