# Deploy to Cloud Run
$ServiceName = "movie-recommendation-server"
$Region = "asia-northeast3" # Seoul Region

Write-Host "🚀 Deploying $ServiceName to Cloud Run ($Region)..." -ForegroundColor Cyan

# Check if gcloud is installed
if (-not (Get-Command "gcloud" -ErrorAction SilentlyContinue)) {
    Write-Error "❌ 'gcloud' CLI not found. Please install Google Cloud SDK first."
    exit 1
}

# Deploy command
# --source .: Deploys the current directory directly (builds on Cloud Build)
# --allow-unauthenticated: Allows public access
gcloud run deploy $ServiceName `
    --source . `
    --region $Region `
    --allow-unauthenticated `
    --port 8080 `
    --memory 2Gi

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ Deployment Successful!" -ForegroundColor Green
    Write-Host "Please check the URL above."
    Write-Host "⚠️  IMPORTANT: Go to Cloud Run Console -> 'Edit & Deploy New Revision' -> 'Variables' and add your OPENAI_API_KEY." -ForegroundColor Yellow
} else {
    Write-Error "`n❌ Deployment Failed."
}
