#!/bin/bash
# --- Rollback GKE Deployment to use v1 image (tagged as latest) ---
# MODIFIED: Removed 'set -e' to prevent exiting on first error during rollback attempt
# MODIFIED: Added deletion of original :v1 tag after retagging to :latest

# Exit on undefined variable or pipe failure, but NOT on error
set -uo pipefail
# Print commands as they execute (optional, comment out '#' to disable)
set -x

# --- Configuration (Copy from your deploy scripts, verify paths) ---
PROJECT_ID="ai-govbot-project" # Make sure this matches your deployment workflow if needed
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

ROLLBACK_SUCCESS=true # Flag to track overall success

# --- Prerequisites Check ---
echo "Checking prerequisites (gcloud, kubectl, jq)..."
# ... (prerequisite checks remain the same) ...
if ! command -v gcloud &> /dev/null; then echo "ERROR: gcloud command not found."; exit 1; fi
if ! command -v kubectl &> /dev/null; then echo "ERROR: kubectl command not found."; exit 1; fi
if ! command -v jq &> /dev/null; then echo "ERROR: jq command not found."; exit 1; fi
echo "Prerequisites met."

# --- GCP/GKE Setup ---
echo "Ensure gcloud is configured..."
# ... (gcloud config checks remain the same) ...
gcloud config get-value project | grep -q "^${PROJECT_ID}$" || \
  (echo "ERROR: gcloud project is not set to ${PROJECT_ID}. Please check PROJECT_ID."; ROLLBACK_SUCCESS=false)

if [ "$ROLLBACK_SUCCESS" = true ]; then
  echo "Configuring kubectl for cluster ${CLUSTER_NAME}..."
  # ... (kubectl config remains the same) ...
  if ! gcloud container clusters describe ${CLUSTER_NAME} --zone ${ZONE} --project=${PROJECT_ID} &> /dev/null; then
    echo "ERROR: GKE Cluster ${CLUSTER_NAME} not found."
    ROLLBACK_SUCCESS=false
  else
    gcloud container clusters get-credentials ${CLUSTER_NAME} --zone ${ZONE} --project ${PROJECT_ID} || \
      (echo "ERROR: Failed to get GKE credentials."; ROLLBACK_SUCCESS=false)
  fi
fi

# --- Rollback Tagging Function ---
rollback_image_tags() {
  # Only proceed if previous steps were okay
  if [ "$ROLLBACK_SUCCESS" = false ]; then return 1; fi

  local IMAGE_BASE=$1
  local IMAGE_TYPE=$2 # "Backend" or "Frontend"
  local CAN_ROLLBACK=true
  echo "--- Starting Rollback Tagging for ${IMAGE_TYPE} (${IMAGE_BASE}) ---"

  # 1. Find current 'latest' digest and retag it to 'v3'
  echo "Finding current 'latest' tag for ${IMAGE_TYPE}..."
  LATEST_DIGEST=$(gcloud artifacts docker images list "${IMAGE_BASE}" --include-tags --format=json | jq -r '.[] | select(.tags[]? == "latest") | .version' || echo "")
  if [[ -n "$LATEST_DIGEST" ]]; then
     echo "Found current latest digest: ${LATEST_DIGEST}. Tagging as v3..."
     (gcloud artifacts docker tags add "${IMAGE_BASE}@${LATEST_DIGEST}" "${IMAGE_BASE}:v3" --quiet && \
      echo "Deleting old latest tag..." && \
      gcloud artifacts docker tags delete "${IMAGE_BASE}:latest" --quiet) || \
      echo "Warning: Failed to retag latest to v3 or delete latest tag for ${IMAGE_TYPE}."
  else
     echo "Warning: No existing latest tag found to move to v3 for ${IMAGE_TYPE}."
  fi

  # 2. Find current 'v1' digest, retag it to 'latest', AND DELETE original 'v1' tag
  echo "Finding current 'v1' tag for ${IMAGE_TYPE}..."
  V1_DIGEST=$(gcloud artifacts docker images list "${IMAGE_BASE}" --include-tags --format=json | jq -r '.[] | select(.tags[]? == "v1") | .version' || echo "")
  if [[ -n "$V1_DIGEST" ]]; then
    echo "Found v1 digest: ${V1_DIGEST}. Tagging as the NEW latest..."
    if gcloud artifacts docker tags add "${IMAGE_BASE}@${V1_DIGEST}" "${IMAGE_BASE}:latest" --quiet; then
        echo "'v1' image digest (${V1_DIGEST}) successfully tagged as 'latest'."
        # --- ADDED: Delete the original v1 tag ---
        echo "Deleting the original 'v1' tag..."
        gcloud artifacts docker tags delete "${IMAGE_BASE}:v1" --quiet || \
            echo "Warning: Failed to delete original 'v1' tag for ${IMAGE_TYPE}."
        # --- End ADDED ---
    else
       echo "ERROR: Failed to tag v1 as latest for ${IMAGE_TYPE}."
       CAN_ROLLBACK=false
       ROLLBACK_SUCCESS=false
    fi
  else
    echo "ERROR: Cannot perform rollback. No image found with tag 'v1' for ${IMAGE_TYPE}."
    CAN_ROLLBACK=false
    ROLLBACK_SUCCESS=false # Mark overall rollback as failed if v1 missing
  fi
  echo "--- Rollback Tagging Complete for ${IMAGE_TYPE} ---"

  # Return success (0) or failure (1) for this specific image's tagging
  if [ "$CAN_ROLLBACK" = true ]; then return 0; else return 1; fi
}

# --- Perform Rollback Tagging ---
# ... (Calling rollback_image_tags remains the same) ...
rollback_image_tags "${BACKEND_IMAGE_NAME_NO_TAG}" "Backend"
BACKEND_ROLLBACK_OK=$?
rollback_image_tags "${FRONTEND_IMAGE_NAME_NO_TAG}" "Frontend"
FRONTEND_ROLLBACK_OK=$?


# --- Apply Kubernetes Deployments (only if tagging for that component was successful) ---
# ... (Applying K8s deployments remains the same) ...
if [ "$ROLLBACK_SUCCESS" = true ]; then
    echo "--- Applying Kubernetes Deployments to Rollback ---"
    if [ $BACKEND_ROLLBACK_OK -eq 0 ]; then
        # ... backend apply/restart ...
        (kubectl apply -f "${BACKEND_DEPLOYMENT_FILE}" -n "${NAMESPACE}" && \
        echo "Restarting backend deployment..." && \
        kubectl rollout restart deployment ai-govbot-backend-deployment -n "${NAMESPACE}") || \
        (echo "ERROR: Failed to apply/restart backend deployment."; ROLLBACK_SUCCESS=false)
    else
        echo "Skipping Backend Kubernetes deployment due to tagging errors."
    fi
    if [ $FRONTEND_ROLLBACK_OK -eq 0 ]; then
        # ... frontend apply/restart ...
        (kubectl apply -f "${FRONTEND_DEPLOYMENT_FILE}" -n "${NAMESPACE}" && \
        echo "Restarting frontend deployment..." && \
        kubectl rollout restart deployment ai-govbot-frontend-deployment -n "${NAMESPACE}") || \
        (echo "ERROR: Failed to apply/restart frontend deployment."; ROLLBACK_SUCCESS=false)
    else
        echo "Skipping Frontend Kubernetes deployment due to tagging errors."
    fi
else
    echo "Skipping Kubernetes deployment apply due to earlier errors."
fi

# --- Monitor Rollback Status (only if successful so far) ---
# ... (Monitoring remains the same) ...
if [ "$ROLLBACK_SUCCESS" = true ]; then
    echo "--- Waiting for Rollback Rollout to Complete ---"
    FINAL_STATUS="Complete"
    if [ $BACKEND_ROLLBACK_OK -eq 0 ]; then
        # ... check backend status ...
        kubectl rollout status deployment/ai-govbot-backend-deployment -n ${NAMESPACE} --timeout=5m || \
            (echo "Warning: Backend deployment rollout failed or timed out."; FINAL_STATUS="Failed/Incomplete")
    fi
    if [ $FRONTEND_ROLLBACK_OK -eq 0 ]; then
         # ... check frontend status ...
         kubectl rollout status deployment/ai-govbot-frontend-deployment -n ${NAMESPACE} --timeout=5m || \
            (echo "Warning: Frontend deployment rollout failed or timed out."; FINAL_STATUS="Failed/Incomplete")
    fi
else
    FINAL_STATUS="Failed/Skipped"
fi


# --- Completion ---
# ... (Completion message remains the same) ...
echo "----------------------------------------"
if [ "$ROLLBACK_SUCCESS" = true ] && [ "$FINAL_STATUS" = "Complete" ]; then
  echo "✅ Rollback Attempt Successful!"
else
  echo "❌ Rollback Attempt Finished with Errors/Warnings or was Skipped."
fi
echo "   Final Status: ${FINAL_STATUS}"
echo "----------------------------------------"
set +x

# Exit with overall success/failure code for GitHub Actions
if [ "$ROLLBACK_SUCCESS" = true ]; then exit 0; else exit 1; fi