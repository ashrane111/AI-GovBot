#!/bin/bash
# --- Deploy Backend to GKE ---

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
K8S_SECRET_NAME="openai-secret"
ENV_FILE=".env" # Path to .env file for secrets

# Backend Specific Config
BACKEND_DOCKERFILE="deployment_scripts/model-deployment/backend/Dockerfile"
BACKEND_DEPLOYMENT_FILE="deployment_scripts/model-deployment/backend/k8s-deployment.yaml"
BACKEND_SERVICE_FILE="deployment_scripts/model-deployment/backend/k8s-service.yaml"
BACKEND_IMAGE_NAME_NO_TAG="${REGION}-docker.pkg.dev/${PROJECT_ID}/${GAR_REPOSITORY_NAME}/ai-govbot-backend"
BACKEND_IMAGE_NAME_LATEST="${BACKEND_IMAGE_NAME_NO_TAG}:latest"

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

# --- GCP/GKE Setup (Idempotent Checks) ---
echo "Ensure gcloud is configured..."
gcloud config get-value project | grep -q "^${PROJECT_ID}$" || \
  (echo "ERROR: gcloud project is not set to ${PROJECT_ID}."; exit 1)
gcloud services enable container.googleapis.com artifactregistry.googleapis.com compute.googleapis.com --project=${PROJECT_ID}

echo "Checking/Configuring GKE Cluster ${CLUSTER_NAME}..."
if ! gcloud container clusters describe ${CLUSTER_NAME} --zone ${ZONE} --project=${PROJECT_ID} &> /dev/null; then
   echo "ERROR: GKE Cluster ${CLUSTER_NAME} not found. Please create it first or check configuration."
   # Optionally add cluster creation logic here if desired, like in the original script
   exit 1
else
   echo "Cluster ${CLUSTER_NAME} exists."
   gcloud container clusters get-credentials ${CLUSTER_NAME} --zone ${ZONE} --project ${PROJECT_ID}
fi

echo "Checking/Configuring GAR Repository ${GAR_REPOSITORY_NAME}..."
if ! gcloud artifacts repositories describe ${GAR_REPOSITORY_NAME} --location=${REGION} --project=${PROJECT_ID} &> /dev/null; then
   echo "ERROR: GAR Repository ${GAR_REPOSITORY_NAME} not found. Please create it first or check configuration."
   # Optionally add repo creation logic here
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

# --- Backend Image Steps ---
echo "--- Starting Backend Deployment ---"
rotate_tags "${BACKEND_IMAGE_NAME_NO_TAG}"

echo "Building and pushing backend image: ${BACKEND_IMAGE_NAME_LATEST}..."
docker buildx build \
  --no-cache \
  --platform linux/amd64,linux/arm64 \
  -t ${BACKEND_IMAGE_NAME_LATEST} \
  -f ${BACKEND_DOCKERFILE} \
  --push \
  . # Build context is current directory (project root)
echo "Backend image build/push complete."

# --- Kubernetes Secret ---
echo "Applying Kubernetes secret '${K8S_SECRET_NAME}' from ${ENV_FILE}..."
if [[ ! -f "${ENV_FILE}" ]]; then echo "ERROR: ${ENV_FILE} not found."; exit 1; fi
if ! grep -q -E '^OPENAI_API_KEY=' "${ENV_FILE}"; then echo "ERROR: OPENAI_API_KEY not found in ${ENV_FILE}."; exit 1; fi
kubectl create secret generic ${K8S_SECRET_NAME} \
  --from-env-file="${ENV_FILE}" \
  --namespace=${NAMESPACE} \
  --dry-run=client -o yaml | kubectl apply -f -
echo "Secret processed."

# --- Kubernetes Deployment ---
echo "Applying Namespace: ${NAMESPACE_FILE}..."
kubectl apply -f "${NAMESPACE_FILE}"

echo "Applying Backend Deployment: ${BACKEND_DEPLOYMENT_FILE}..."
kubectl apply -f "${BACKEND_DEPLOYMENT_FILE}" -n "${NAMESPACE}"
kubectl rollout restart deployment ai-govbot-backend-deployment -n "${NAMESPACE}" # Force restart

echo "Applying Backend Service: ${BACKEND_SERVICE_FILE}..."
kubectl apply -f "${BACKEND_SERVICE_FILE}" -n "${NAMESPACE}"

echo "Waiting for backend deployment rollout..."
kubectl rollout status deployment/ai-govbot-backend-deployment -n ${NAMESPACE} --timeout=5m

echo "Retrieving Backtend External IP..."
EXTERNAL_IP=""
EXTERNAL_IP=$(kubectl get service "${BACKEND_SERVICE_NAME}" -n "${NAMESPACE}" -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")

# --- Completion ---
echo "----------------------------------------"
echo "✅ Backend Deployment Complete!"
echo "----------------------------------------"
set +x