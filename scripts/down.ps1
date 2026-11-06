$ErrorActionPreference = "Stop"

Write-Host "Stopping cloud-project cluster..."
k3d cluster stop cloud-project
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host "Cluster stopped. Data and cluster configuration are preserved."
