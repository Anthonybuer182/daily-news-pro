# =============================================================================
# Daily News Pro - Build frontend locally and upload dist to Ubuntu server
#
# Usage (run on your Windows machine):
#   .\build-and-upload.ps1                                          # use defaults
#   .\build-and-upload.ps1 -Server "user@1.2.3.4" -Remote "/opt/daily-news-pro"
#
# What it does: npm run build locally (avoids OOM on a 2GB server),
#               scp the dist folder, then ssh-trigger deploy.sh on the server.
# =============================================================================
param(
    [string]$Server = "root@YOUR_SERVER_IP",
    [string]$Remote = "/opt/daily-news-pro",
    [switch]$SkipDeploy
)

$ErrorActionPreference = "Stop"

Write-Host ">>> [1/3] Build frontend dist locally ..." -ForegroundColor Cyan
Push-Location (Join-Path $PSScriptRoot "frontend")
try {
    if (-not (Test-Path "node_modules")) {
        Write-Host "    Running npm install ..."
        npm install
    }
    npm run build
    if (-not (Test-Path "dist")) {
        throw "Build failed: frontend/dist not found"
    }
}
finally {
    Pop-Location
}

$distLocal = Join-Path $PSScriptRoot "frontend\dist"
$distRemote = "$Remote/frontend/dist"

Write-Host ">>> [2/3] Upload dist to $Server`:$distRemote ..." -ForegroundColor Cyan
# Ensure remote directory exists
ssh $Server "mkdir -p $distRemote"
# Upload dist contents (scp -r with wildcards is unreliable on Windows, so iterate)
if ($IsWindows -or $env:OS -eq "Windows_NT") {
    Get-ChildItem -Path $distLocal -Force | ForEach-Object {
        scp -r $_.FullName "$Server`:$distRemote/"
    }
} else {
    tar -C $distLocal -czf - . | ssh $Server "tar -C $distRemote -xzf -"
}

if ($SkipDeploy) {
    Write-Host ">>> Skipped server deploy (-SkipDeploy)" -ForegroundColor Yellow
    return
}

Write-Host ">>> [3/3] Trigger deploy.sh on server ..." -ForegroundColor Cyan
ssh $Server "cd $Remote && sudo bash deploy.sh"

Write-Host "`n=== Done ===`nVisit: http://<server-ip>:8000" -ForegroundColor Green
