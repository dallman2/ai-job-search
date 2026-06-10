#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

CLUSTER_NAME="job-search-local"
IMAGE_NAME="job-search-db:latest"

echo "=== Job Search Database — Cluster Start ==="
echo ""

cd "$REPO_ROOT"

if kind get clusters 2>/dev/null | grep -qx "$CLUSTER_NAME"; then
    echo "[skip] kind cluster '$CLUSTER_NAME' already exists"
else
    echo "[1/5] Creating kind cluster '$CLUSTER_NAME'..."
    kind create cluster --config k8s/kind-config.yaml --name "$CLUSTER_NAME"
fi

echo "[2/5] Building Docker image..."
docker build -t "$IMAGE_NAME" db/

echo "[3/5] Loading image into kind..."
kind load docker-image "$IMAGE_NAME" --name "$CLUSTER_NAME"

echo "[4/5] Applying Kubernetes manifests..."
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/pv.yaml
kubectl apply -f k8s/pvc.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

echo "[5/5] Waiting for deployment to be ready..."
kubectl rollout status deployment/sqlite-api -n job-search --timeout=60s

echo ""
echo "=== Cluster ready ==="
echo "API URL: http://localhost:30080"
echo "Verify:  python3 db/client.py health"
echo ""
echo "To stop:  kind delete cluster --name $CLUSTER_NAME"
echo "Data persists at: $REPO_ROOT/data/job-search.db"
