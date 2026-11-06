$ErrorActionPreference = "Stop"

Write-Host "Checking k3d cluster..."
$clusters = k3d cluster list 2>$null | Out-String

if ($clusters -match "cloud-project") {
    k3d cluster start cloud-project
} else {
    k3d cluster create --config cluster/k3d.yaml
}
if ($LASTEXITCODE -ne 0) { exit 1 }

kubectl wait --for=condition=Ready nodes --all --timeout=180s
if ($LASTEXITCODE -ne 0) { exit 1 }

foreach ($ns in @("data", "pipeline", "app")) {
    kubectl create namespace $ns --dry-run=client -o yaml | kubectl apply -f -
    if ($LASTEXITCODE -ne 0) { exit 1 }
}

Write-Host "Deploying SeaweedFS..."
kubectl apply -f storage/seaweedfs.yaml
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host "Building API image..."
docker build -t command-parser:v2 .
if ($LASTEXITCODE -ne 0) { exit 1 }

k3d image import command-parser:v2 -c cloud-project
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host "Installing NGINX Ingress..."
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.13.3/deploy/static/provider/cloud/deploy.yaml
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host "Applying Kubernetes manifests..."
kubectl apply -f k8s/
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host "Project deployment completed."
