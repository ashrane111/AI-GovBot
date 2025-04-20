#!/bin/bash
# --- Rollback GKE Deployment to use v1 image (tagged as latest) ---

# Exit on error, undefined variable, or pipe failure
set -euo pipefail
# Print commands as they execute (optional, comment out '#' to disable)
set -x

# --- Configuration (Copy from your deploy scripts, verify paths) ---
PROJECT_ID="data-pipeline-deployment-trial"
ZONE="us-east1-d"
REGION="us-east1"
CLUSTER_NAME="ai-govbot-cluster"
GAR_REPOSITORY_NAME="ai-govbot-repo"
NAMESPACE="mlscopers"

# K8s manifest paths
BACKEND_DEPLOYMENT_FILE="deployment_scripts/model-deployment/backend/k8s-deployment.yaml"
FRONTEND_DEPLOYMENT_FILE="deployment_scripts/model-deployment/frontend/k8s-deployment.yaml"

# GAR Image Names (Base names without tags)
BACKEND_IMAGE_NAME_NO_TAG="${REGION}-docker.pkg.dev/${PROJECT_ID}/${GAR_REPOSITORY_NAME}/ai-govbot-backend"
FRONTEND_IMAGE_NAME_NO_TAG="${REGION}-docker.pkg.dev/${PROJECT_ID}/${GAR_REPOSITORY_NAME}/ai-govbot-frontend"

# --- Prerequisites Check ---
echo "Checking prerequisites (gcloud, kubectl, jq)..."
if ! command -v gcloud &> /dev/null; then echo "ERROR: gcloud command not found."; exit 1; fi
if ! command -v kubectl &> /dev/null; then echo "ERROR: kubectl command not found."; exit 1; fi
if ! command -v jq &> /dev/null; then echo "ERROR: jq command not found."; exit 1; fi
echo "Prerequisites met."

# --- GCP/GKE Setup ---
echo "Ensure gcloud is configured..."
gcloud config get-value project | grep -q "^${PROJECT_ID}$" || \
  (echo "ERROR: gcloud project is not set to ${PROJECT_ID}."; exit 1)

echo "Configuring kubectl for cluster ${CLUSTER_NAME}..."
# Ensure cluster exists before getting credentials
if ! gcloud container clusters describe ${CLUSTER_NAME} --zone ${ZONE} --project=${PROJECT_ID} &> /dev/null; then
   echo "ERROR: GKE Cluster ${CLUSTER_NAME} not found."
   exit 1
fi
gcloud container clusters get-credentials ${CLUSTER_NAME} --zone ${ZONE} --project ${PROJECT_ID}

# --- Rollback Tagging Function ---
rollback_image_tags() {
  local IMAGE_BASE=$1
  echo "--- Starting Rollback Tagging for ${IMAGE_BASE} ---"

  # 1. Find current 'latest' digest and retag it to 'v3'
  echo "Finding current 'latest' tag..."
  LATEST_DIGEST=$(gcloud artifacts docker images list "${IMAGE_BASE}" --include-tags --format=json | jq -r '.[] | select(.tags[]? == "latest") | .version' || echo "")
  if [[ -n "$LATEST_DIGEST" ]]; then
     echo "Found current latest digest: ${LATEST_DIGEST}. Tagging as v3..."
     gcloud artifacts docker tags add "${IMAGE_BASE}@${LATEST_DIGEST}" "${IMAGE_BASE}:v3" --quiet
     echo "Deleting old latest tag..."
     gcloud artifacts docker tags delete "${IMAGE_BASE}:latest" --quiet
  else
     echo "Warning: No existing latest tag found to move to v3 for ${IMAGE_BASE}."
     # Continue, maybe v1 exists and can become latest
  fi

  # 2. Find current 'v1' digest and retag it to 'latest'
  echo "Finding current 'v1' tag..."
  V1_DIGEST=$(gcloud artifacts docker images list "${IMAGE_BASE}" --include-tags --format=json | jq -r '.[] | select(.tags[]? == "v1") | .version' || echo "")
  if [[ -n "$V1_DIGEST" ]]; then
    echo "Found v1 digest: ${V1_DIGEST}. Tagging as the NEW latest..."
    gcloud artifacts docker tags add "${IMAGE_BASE}@${V1_DIGEST}" "${IMAGE_BASE}:latest" --quiet
    # IMPORTANT: Do NOT delete the v1 tag here, as it's the one we want to deploy
    echo "'v1' image is now also tagged as 'latest'."
  else
    echo "ERROR: Cannot perform rollback. No image found with tag 'v1' for ${IMAGE_BASE}."
    exit 1 # Exit if the target rollback image doesn't exist
  fi
  echo "--- Rollback Tagging Complete for ${IMAGE_BASE} ---"
}

# --- Perform Rollback Tagging ---
rollback_image_tags "${BACKEND_IMAGE_NAME_NO_TAG}"
rollback_image_tags "${FRONTEND_IMAGE_NAME_NO_TAG}"

# --- Apply Kubernetes Deployments (using the new :latest tag) ---
echo "--- Applying Kubernetes Deployments to Rollback ---"

# Apply Backend Deployment (will pull the new :latest image)
echo "Applying Backend Deployment: ${BACKEND_DEPLOYMENT_FILE}..."
kubectl apply -f "${BACKEND_DEPLOYMENT_FILE}" -n "${NAMESPACE}"
echo "Restarting backend deployment to ensure image update..."
kubectl rollout restart deployment ai-govbot-backend-deployment -n "${NAMESPACE}"

# Apply Frontend Deployment (will pull the new :latest image)
echo "Applying Frontend Deployment: ${FRONTEND_DEPLOYMENT_FILE}..."
kubectl apply -f "${FRONTEND_DEPLOYMENT_FILE}" -n "${NAMESPACE}"
echo "Restarting frontend deployment to ensure image update..."
kubectl rollout restart deployment ai-govbot-frontend-deployment -n "${NAMESPACE}"

# --- Monitor Rollback Status ---
echo "--- Waiting for Rollback Rollout to Complete ---"
echo "Checking backend rollout status..."
kubectl rollout status deployment/ai-govbot-backend-deployment -n ${NAMESPACE} --timeout=5m

echo "Checking frontend rollout status..."
kubectl rollout status deployment/ai-govbot-frontend-deployment -n ${NAMESPACE} --timeout=5m

# --- Completion ---
echo "----------------------------------------"
echo "✅ Rollback to v1 (now tagged as latest) Complete!"
echo "   Deployments restarted and status checked."
echo "----------------------------------------"
set +x