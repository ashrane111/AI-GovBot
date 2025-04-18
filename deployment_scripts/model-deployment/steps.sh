#!/bin/bash
set -euo pipefail
set -x

PROJECT_ID="data-pipeline-deployment-trial"
ZONE="us-east1-d"


# --- Configuration ---
NAMESPACE="mlscopers"
DEPLOYMENT_DIR="deployment_scripts/model-deployment"
BACKEND_DEPLOYMENT_FILE="${DEPLOYMENT_DIR}/backend/k8s-deployment.yaml"
BACKEND_SERVICE_FILE="${DEPLOYMENT_DIR}/backend/k8s-service.yaml"
FRONTEND_DEPLOYMENT_FILE="${DEPLOYMENT_DIR}/frontend/k8s-deployment.yaml"
FRONTEND_SERVICE_FILE="${DEPLOYMENT_DIR}/frontend/k8s-service.yaml"
NAMESPACE_FILE="${DEPLOYMENT_DIR}/k8s-namespace.yaml"

# --- Prerequisites ---
# 1. Ensure kubectl is installed and configured for your GKE cluster.
#    Example: gcloud container clusters get-credentials ai-govbot-cluster --region us-east1 --project data-pipeline-deployment-trial
# 2. Ensure the OPENAI_API_KEY placeholder in backend deployment YAML is replaced if using that method.
#    This script DOES NOT handle secret injection.

# --- Deployment Steps ---
echo "Starting Kubernetes deployment to namespace: ${NAMESPACE}..."

# Apply Namespace
echo "Applying Namespace: ${NAMESPACE_FILE}..."
kubectl apply -f "${NAMESPACE_FILE}"

# Apply Backend resources
echo "Applying Backend Deployment: ${BACKEND_DEPLOYMENT_FILE}..."
kubectl apply -f "${BACKEND_DEPLOYMENT_FILE}" -n "${NAMESPACE}"

echo "Applying Backend Service: ${BACKEND_SERVICE_FILE}..."
kubectl apply -f "${BACKEND_SERVICE_FILE}" -n "${NAMESPACE}"

# Apply Frontend resources
echo "Applying Frontend Deployment: ${FRONTEND_DEPLOYMENT_FILE}..."
kubectl apply -f "${FRONTEND_DEPLOYMENT_FILE}" -n "${NAMESPACE}"

echo "Applying Frontend Service: ${FRONTEND_SERVICE_FILE}..."
kubectl apply -f "${FRONTEND_SERVICE_FILE}" -n "${NAMESPACE}"

echo "----------------------------------------"
echo "Kubernetes deployment applied successfully!"
echo "----------------------------------------"
echo "You can check the status using:"
echo "kubectl get all -n ${NAMESPACE}"
echo "kubectl get service ai-govbot-frontend-service -n ${NAMESPACE}"
echo "Note: It might take a minute or two for the LoadBalancer IP to become available."