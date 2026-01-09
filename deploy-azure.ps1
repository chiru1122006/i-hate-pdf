# Azure-specific deployment script for PowerShell
# Run this script to deploy to Azure App Service

param(
    [Parameter(Mandatory=$true)]
    [string]$ResourceGroup,
    
    [Parameter(Mandatory=$true)]
    [string]$AppName,
    
    [string]$Location = "eastus",
    [string]$Sku = "B1"
)

Write-Host "Starting Azure deployment for Word to PDF Converter..." -ForegroundColor Green

# Check if Azure CLI is installed
if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Azure CLI is not installed." -ForegroundColor Red
    Write-Host "Install from: https://docs.microsoft.com/cli/azure/install-azure-cli" -ForegroundColor Yellow
    exit 1
}

# Login to Azure
Write-Host "`nLogging in to Azure..." -ForegroundColor Cyan
az login

# Create resource group
Write-Host "`nCreating resource group: $ResourceGroup in $Location..." -ForegroundColor Cyan
az group create --name $ResourceGroup --location $Location

# Create App Service Plan
$planName = "$AppName-plan"
Write-Host "`nCreating App Service Plan: $planName (SKU: $Sku)..." -ForegroundColor Cyan
az appservice plan create `
    --name $planName `
    --resource-group $ResourceGroup `
    --is-linux `
    --sku $Sku `
    --location $Location

# Create Web App
Write-Host "`nCreating Web App: $AppName..." -ForegroundColor Cyan
az webapp create `
    --resource-group $ResourceGroup `
    --plan $planName `
    --name $AppName `
    --runtime "PYTHON:3.11"

# Configure deployment from local Git
Write-Host "`nConfiguring deployment..." -ForegroundColor Cyan
az webapp deployment source config-local-git `
    --name $AppName `
    --resource-group $ResourceGroup

# Set startup command
Write-Host "`nConfiguring startup command..." -ForegroundColor Cyan
az webapp config set `
    --resource-group $ResourceGroup `
    --name $AppName `
    --startup-file "gunicorn -w 2 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8000"

# Configure app settings
Write-Host "`nConfiguring app settings..." -ForegroundColor Cyan
az webapp config appsettings set `
    --resource-group $ResourceGroup `
    --name $AppName `
    --settings `
        SCM_DO_BUILD_DURING_DEPLOYMENT=true `
        WEBSITES_PORT=8000 `
        PORT=8000

# Enable health check
Write-Host "`nEnabling health check..." -ForegroundColor Cyan
az webapp config set `
    --resource-group $ResourceGroup `
    --name $AppName `
    --health-check-path /health

# Get deployment credentials
Write-Host "`n" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host "Deployment Setup Complete!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green

$deployUser = az webapp deployment list-publishing-credentials --name $AppName --resource-group $ResourceGroup --query publishingUserName -o tsv
$deployPassword = az webapp deployment list-publishing-credentials --name $AppName --resource-group $ResourceGroup --query publishingPassword -o tsv
$gitUrl = az webapp deployment source config-local-git --name $AppName --resource-group $ResourceGroup --query url -o tsv

Write-Host "`nYour app URL: https://$AppName.azurewebsites.net" -ForegroundColor Cyan

Write-Host "`n--- Deploy using Git ---" -ForegroundColor Yellow
Write-Host "1. Add Azure as a remote:" -ForegroundColor White
Write-Host "   git remote add azure $gitUrl" -ForegroundColor Gray
Write-Host "`n2. Push to deploy:" -ForegroundColor White
Write-Host "   git add ." -ForegroundColor Gray
Write-Host "   git commit -m 'Deploy to Azure'" -ForegroundColor Gray
Write-Host "   git push azure main" -ForegroundColor Gray
Write-Host "`nUsername: $deployUser" -ForegroundColor White
Write-Host "Password: $deployPassword" -ForegroundColor White

Write-Host "`n--- Or deploy using Docker ---" -ForegroundColor Yellow
Write-Host "See AZURE_DEPLOYMENT.md for Docker deployment instructions" -ForegroundColor White

Write-Host "`n================================================" -ForegroundColor Green
