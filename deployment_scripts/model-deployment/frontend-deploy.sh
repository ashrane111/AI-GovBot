#!/bin/bash
# --- Deploy Frontend to GKE & Get External IP ---

# Exit on error, undefined variable, or pipe failure
set -euo pipefail
# Print commands as they execute (optional, comment out '#' to disable)
set -x

# --- Configuration ---
PROJECT_ID="data-pipeline-deployment-trial"
ZONE="us-east1-d"
REGION="us-east1"
CLUSTER_NAME="ai-govbot-cluster"
GAR_REPOSITORY_NAME="ai-govbot-repo"
NAMESPACE="mlscopers"

# Frontend Specific Config
FRONTEND_DOCKERFILE="deployment_scripts/model-deployment/frontend/Dockerfile"
FRONTEND_DEPLOYMENT_FILE="deployment_scripts/model-deployment/frontend/k8s-deployment.yaml"
FRONTEND_SERVICE_FILE="deployment_scripts/model-deployment/frontend/k8s-service.yaml"
FRONTEND_IMAGE_NAME_NO_TAG="${REGION}-docker.pkg.dev/${PROJECT_ID}/${GAR_REPOSITORY_NAME}/ai-govbot-frontend"
FRONTEND_IMAGE_NAME_LATEST="${FRONTEND_IMAGE_NAME_NO_TAG}:latest"
FRONTEND_SERVICE_NAME="ai-govbot-frontend-service" # Name defined in frontend/k8s-service.yaml

# Common Config
NAMESPACE_FILE="deployment_scripts/model-deployment/k8s-namespace.yaml"
GAR_REPO_PATH_PREFIX="${REGION}-docker.pkg.dev"

# --- Prerequisites Check ---
echo "Checking prerequisites (gcloud, kubectl, docker, jq)..."
if ! command -v gcloud &> /dev/null; then echo "ERROR: gcloud command not found."; exit 1; fi
if ! command -v kubectl &> /dev/null; then echo "ERROR: kubectl command not found."; exit 1; fi
if ! command -v docker &> /dev/null; then echo "ERROR: docker command not found."; exit 1; fi
if ! command -v jq &> /dev/null; then echo "ERROR: jq command not found."; exit 1; fi # Added jq check
if ! docker buildx version &> /dev/null; then echo "ERROR: docker buildx not available."; exit 1; fi
echo "Prerequisites met."

# --- GCP/GKE Setup (Idempotent Checks - can be skipped if backend script ran) ---
echo "Ensure gcloud is configured (may skip if backend script ran)..."
gcloud config get-value project | grep -q "^${PROJECT_ID}$" || \
  (echo "ERROR: gcloud project is not set to ${PROJECT_ID}."; exit 1)
gcloud services enable container.googleapis.com artifactregistry.googleapis.com compute.googleapis.com --project=${PROJECT_ID}

echo "Checking/Configuring GKE Cluster ${CLUSTER_NAME} (may skip if backend script ran)..."
if ! gcloud container clusters describe ${CLUSTER_NAME} --zone ${ZONE} --project=${PROJECT_ID} &> /dev/null; then
   echo "ERROR: GKE Cluster ${CLUSTER_NAME} not found."
   exit 1
else
   echo "Cluster ${CLUSTER_NAME} exists."
   gcloud container clusters get-credentials ${CLUSTER_NAME} --zone ${ZONE} --project ${PROJECT_ID}
fi

echo "Checking/Configuring GAR Repository ${GAR_REPOSITORY_NAME} (may skip if backend script ran)..."
if ! gcloud artifacts repositories describe ${GAR_REPOSITORY_NAME} --location=${REGION} --project=${PROJECT_ID} &> /dev/null; then
   echo "ERROR: GAR Repository ${GAR_REPOSITORY_NAME} not found."
   exit 1
else
    echo "GAR Repository ${GAR_REPOSITORY_NAME} exists."
    gcloud auth configure-docker ${GAR_REPO_PATH_PREFIX} --project=${PROJECT_ID}
fi

# --- Tag Rotation Function ---
rotate_tags() {
  local IMAGE_BASE=$1
  echo "Rotating tags for ${IMAGE_BASE}"
  gcloud artifacts docker tags delete "${IMAGE_BASE}:v2" --quiet || echo "No existing v2 tag to delete."
  V1_DIGEST=$(gcloud artifacts docker images list "${IMAGE_BASE}" --include-tags --format=json | jq -r '.[] | select(.tags[]? == "v1") | .version' || echo "")
  if [[ -n "$V1_DIGEST" ]]; then
    echo "Found v1 digest: ${V1_DIGEST}. Tagging as v2..."
    gcloud artifacts docker tags add "${IMAGE_BASE}@${V1_DIGEST}" "${IMAGE_BASE}:v2" --quiet
    gcloud artifacts docker tags delete "${IMAGE_BASE}:v1" --quiet
  else echo "No existing v1 tag found."; fi
  LATEST_DIGEST=$(gcloud artifacts docker images list "${IMAGE_BASE}" --include-tags --format=json | jq -r '.[] | select(.tags[]? == "latest") | .version' || echo "")
  if [[ -n "$LATEST_DIGEST" ]]; then
     echo "Found latest digest: ${LATEST_DIGEST}. Tagging as v1..."
     gcloud artifacts docker tags add "${IMAGE_BASE}@${LATEST_DIGEST}" "${IMAGE_BASE}:v1" --quiet
     gcloud artifacts docker tags delete "${IMAGE_BASE}:latest" --quiet
  else echo "No existing latest tag found."; fi
  echo "Tag rotation complete for ${IMAGE_BASE}."
}

# --- Frontend Image Steps ---
echo "--- Starting Frontend Deployment ---"
rotate_tags "${FRONTEND_IMAGE_NAME_NO_TAG}"

echo "Building and pushing frontend image: ${FRONTEND_IMAGE_NAME_LATEST}..."
docker buildx build \
  --no-cache \
  --platform linux/amd64,linux/arm64 \
  -t ${FRONTEND_IMAGE_NAME_LATEST} \
  -f ${FRONTEND_DOCKERFILE} \
  --push \
  . # Build context is current directory (project root)
echo "Frontend image build/push complete."

# --- Kubernetes Deployment ---
echo "Applying Namespace: ${NAMESPACE_FILE} (may skip if backend script ran)..."
kubectl apply -f "${NAMESPACE_FILE}"

echo "Applying Frontend Deployment: ${FRONTEND_DEPLOYMENT_FILE}..."
kubectl apply -f "${FRONTEND_DEPLOYMENT_FILE}" -n "${NAMESPACE}"
kubectl rollout restart deployment ai-govbot-frontend-deployment -n "${NAMESPACE}" # Force restart

echo "Applying Frontend Service: ${FRONTEND_SERVICE_FILE}..."
kubectl apply -f "${FRONTEND_SERVICE_FILE}" -n "${NAMESPACE}"

echo "Waiting for frontend deployment rollout..."
kubectl rollout status deployment/ai-govbot-frontend-deployment -n ${NAMESPACE} --timeout=5m

# --- Get Frontend External IP ---
echo "Retrieving Frontend External IP..."
EXTERNAL_IP=""
TIMEOUT=300 # Timeout in seconds (5 minutes)
COUNT=0
INTERVAL=10 # Check every 10 seconds

while [ -z "$EXTERNAL_IP" ]; do
    if [ $COUNT -ge $((TIMEOUT / INTERVAL)) ]; then
        echo "ERROR: Timeout waiting for external IP for service ${FRONTEND_SERVICE_NAME}."
        exit 1
    fi
    # Attempt to get the IP address
    EXTERNAL_IP=$(kubectl get service "${FRONTEND_SERVICE_NAME}" -n "${NAMESPACE}" -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")

    if [ -z "$EXTERNAL_IP" ]; then
        echo "Waiting for external IP... (${COUNT} / $((TIMEOUT / INTERVAL)))"
        sleep $INTERVAL
        COUNT=$((COUNT + 1))
    else
        # Validate if it looks like an IP address
        if [[ "$EXTERNAL_IP" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
            echo "✅ External IP Found: ${EXTERNAL_IP}"
        else
             echo "Waiting for valid external IP (currently: '${EXTERNAL_IP}')... (${COUNT} / $((TIMEOUT / INTERVAL)))"
             EXTERNAL_IP="" # Reset if not a valid IP yet (e.g., <pending>)
             sleep $INTERVAL
             COUNT=$((COUNT + 1))
        fi
    fi
done


# --- Completion ---
echo "----------------------------------------"
echo "✅ Frontend Deployment Complete!"
echo "   Frontend External IP: ${EXTERNAL_IP}"
echo "   Access Frontend at: http://${EXTERNAL_IP}" 
echo "----------------------------------------"
set +x