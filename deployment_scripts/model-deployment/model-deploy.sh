#!/bin/bash

# Exit on error, undefined variable, or pipe failure
set -euo pipefail
# Print commands as they execute (optional, comment out '#' to disable)
set -x

# --- Configuration (Review and adjust if necessary) ---
PROJECT_ID="data-pipeline-deployment-trial"
ZONE="us-east1-d"                            # Zone for GKE Cluster
REGION="us-east1"                            # Region for GAR Repository (must contain ZONE)
CLUSTER_NAME="ai-govbot-cluster"       # Name for your GKE cluster
GAR_REPOSITORY_NAME="ai-govbot-repo"         # Name for your GAR repository
NAMESPACE="mlscopers"                        # Kubernetes namespace
K8S_SECRET_NAME="openai-secret"              # Name for the K8s secret holding the API key

# Define Dockerfile Paths
BACKEND_DOCKERFILE="deployment_scripts/model-deployment/backend/Dockerfile"
FRONTEND_DOCKERFILE="deployment_scripts/model-deployment/frontend/Dockerfile"

# Define K8s manifest paths
NAMESPACE_FILE="deployment_scripts/model-deployment/k8s-namespace.yaml"
BACKEND_DEPLOYMENT_FILE="deployment_scripts/model-deployment/backend/k8s-deployment.yaml"
BACKEND_SERVICE_FILE="deployment_scripts/model-deployment/backend/k8s-service.yaml"
FRONTEND_DEPLOYMENT_FILE="deployment_scripts/model-deployment/frontend/k8s-deployment.yaml"
FRONTEND_SERVICE_FILE="deployment_scripts/model-deployment/frontend/k8s-service.yaml"

# Define GAR Image Names (using variables defined above)
BACKEND_IMAGE_NAME_NO_TAG="${REGION}-docker.pkg.dev/${PROJECT_ID}/${GAR_REPOSITORY_NAME}/ai-govbot-backend"
FRONTEND_IMAGE_NAME_NO_TAG="${REGION}-docker.pkg.dev/${PROJECT_ID}/${GAR_REPOSITORY_NAME}/ai-govbot-frontend"
BACKEND_IMAGE_NAME_LATEST="${BACKEND_IMAGE_NAME_NO_TAG}:latest"
FRONTEND_IMAGE_NAME_LATEST="${FRONTEND_IMAGE_NAME_NO_TAG}:latest"
GAR_REPO_PATH_PREFIX="${REGION}-docker.pkg.dev" # Used for docker login config

# --- Prerequisites Check ---
echo "Checking prerequisites (gcloud, kubectl, docker)..."
if ! command -v gcloud &> /dev/null; then echo "ERROR: gcloud command not found. Please install Google Cloud SDK."; exit 1; fi
if ! command -v kubectl &> /dev/null; then echo "ERROR: kubectl command not found. Please install kubectl."; exit 1; fi
if ! command -v docker &> /dev/null; then echo "ERROR: docker command not found. Please install Docker."; exit 1; fi
if ! docker buildx version &> /dev/null; then echo "ERROR: docker buildx not available. Ensure Docker is up-to-date or setup buildx."; exit 1; fi

echo "Ensure you are logged into gcloud (run 'gcloud auth login' if needed)."
echo "Ensure gcloud project is set to ${PROJECT_ID} (run 'gcloud config set project ${PROJECT_ID}' if needed)."
gcloud config get-value project | grep -q "^${PROJECT_ID}$" || \
  (echo "ERROR: gcloud project is not set to ${PROJECT_ID}. Please run 'gcloud config set project ${PROJECT_ID}'."; exit 1)

# --- GCP Project Setup (Enable APIs - Run once if needed) ---
echo "Ensuring required APIs are enabled..."
gcloud services enable container.googleapis.com artifactregistry.googleapis.com compute.googleapis.com --project=${PROJECT_ID}

# --- Create Zonal GKE Cluster ---
echo "Checking/Creating Zonal GKE cluster ${CLUSTER_NAME} in zone ${ZONE}..."
if ! gcloud container clusters describe ${CLUSTER_NAME} --zone ${ZONE} --project=${PROJECT_ID} &> /dev/null; then
    gcloud container clusters create ${CLUSTER_NAME} \
        --project=${PROJECT_ID} \
        --zone=${ZONE} \
        --num-nodes=1 \
        --machine-type=e2-standard-4 \
        --disk-type=pd-standard \
        --scopes="https://www.googleapis.com/auth/cloud-platform"
    echo "Cluster ${CLUSTER_NAME} created."
else
    echo "Cluster ${CLUSTER_NAME} already exists in zone ${ZONE}."
fi

# --- Configure kubectl ---
echo "Configuring kubectl for cluster ${CLUSTER_NAME}..."
gcloud container clusters get-credentials ${CLUSTER_NAME} --zone ${ZONE} --project ${PROJECT_ID}

# --- Create Regional GAR Repository ---
echo "Checking/Creating Artifact Registry repository ${GAR_REPOSITORY_NAME} in region ${REGION}..."
if ! gcloud artifacts repositories describe ${GAR_REPOSITORY_NAME} --location=${REGION} --project=${PROJECT_ID} &> /dev/null; then
    gcloud artifacts repositories create ${GAR_REPOSITORY_NAME} \
        --project=${PROJECT_ID} \
        --repository-format=docker \
        --location=${REGION} \
        --description="Docker repository for AI-GovBot application"
    echo "Artifact Registry repository created."
else
    echo "Artifact Registry repository ${GAR_REPOSITORY_NAME} already exists in region ${REGION}."
fi
echo "Artifact Registry repository path: ${REGION}-docker.pkg.dev/${PROJECT_ID}/${GAR_REPOSITORY_NAME}"

# --- Configure Docker for Artifact Registry ---
echo "Configuring Docker credentials for Artifact Registry: ${GAR_REPO_PATH_PREFIX}..."
gcloud auth configure-docker ${GAR_REPO_PATH_PREFIX} --project=${PROJECT_ID}

# --- Implement latest -> v1 -> v2 Tag Rotation ---
rotate_tags() {
  local IMAGE_BASE=$1
  echo "Rotating tags for ${IMAGE_BASE}"

  # 1. Delete existing v2 tag
  echo "Attempting to delete existing v2 tag..."
  gcloud artifacts docker tags delete "${IMAGE_BASE}:v2" --quiet || echo "No existing v2 tag to delete."

  # 2. Retag existing v1 to v2
  echo "Attempting to retag v1 to v2..."
  V1_DIGEST=$(gcloud artifacts docker images list "${IMAGE_BASE}" --include-tags --format=json | jq -r '.[] | select(.tags[]? == "v1") | .version' || echo "")
  if [[ -n "$V1_DIGEST" ]]; then
    echo "Found v1 digest: ${V1_DIGEST}. Tagging as v2..."
    gcloud artifacts docker tags add "${IMAGE_BASE}@${V1_DIGEST}" "${IMAGE_BASE}:v2" --quiet
    echo "Deleting old v1 tag..."
    gcloud artifacts docker tags delete "${IMAGE_BASE}:v1" --quiet
  else
    echo "No existing v1 tag found."
  fi

  # 3. Retag existing latest to v1
  echo "Attempting to retag latest to v1..."
  LATEST_DIGEST=$(gcloud artifacts docker images list "${IMAGE_BASE}" --include-tags --format=json | jq -r '.[] | select(.tags[]? == "latest") | .version' || echo "")
  if [[ -n "$LATEST_DIGEST" ]]; then
     echo "Found latest digest: ${LATEST_DIGEST}. Tagging as v1..."
     gcloud artifacts docker tags add "${IMAGE_BASE}@${LATEST_DIGEST}" "${IMAGE_BASE}:v1" --quiet
     echo "Deleting old latest tag..."
     gcloud artifacts docker tags delete "${IMAGE_BASE}:latest" --quiet
  else
     echo "No existing latest tag found."
  fi
  echo "Tag rotation complete for ${IMAGE_BASE}."
}

rotate_tags "${BACKEND_IMAGE_NAME_NO_TAG}"
rotate_tags "${FRONTEND_IMAGE_NAME_NO_TAG}"

# --- Build and Push New ':latest' Images using docker buildx ---
echo "Building and pushing multi-arch backend image to ${BACKEND_IMAGE_NAME_LATEST}..."
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t ${BACKEND_IMAGE_NAME_LATEST} \
  -f ${BACKEND_DOCKERFILE} \
  --push \
  . # Build context is current directory (project root)

echo "Building and pushing multi-arch frontend image to ${FRONTEND_IMAGE_NAME_LATEST}..."
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t ${FRONTEND_IMAGE_NAME_LATEST} \
  -f ${FRONTEND_DOCKERFILE} \
  --push \
  . # Build context is current directory (project root)

echo "Docker images built and pushed to GAR successfully."

# --- Create/Update Kubernetes Secret from .env file ---
echo "Preparing Kubernetes secret '${K8S_SECRET_NAME}' by reading from .env file..."

# Define expected .env file path
ENV_FILE=".env"

# 1. Check if .env file exists
if [[ ! -f "${ENV_FILE}" ]]; then
    echo "ERROR: ${ENV_FILE} file not found in the current directory."
    echo "Please create it with your OPENAI_API_KEY."
    exit 1
fi

# 2. Check if OPENAI_API_KEY is present in the .env file
if ! grep -q -E '^OPENAI_API_KEY=' "${ENV_FILE}"; then
    echo "ERROR: OPENAI_API_KEY not found in ${ENV_FILE}."
    echo "Please ensure the file contains a line like 'OPENAI_API_KEY=sk-...'"
    exit 1
fi

# 3. Apply the secret directly using the .env file
#    kubectl apply handles create/update idempotently.
echo "Applying Kubernetes secret '${K8S_SECRET_NAME}' from ${ENV_FILE}..."
kubectl create secret generic ${K8S_SECRET_NAME} \
  --from-env-file="${ENV_FILE}" \
  --namespace=${NAMESPACE} \
  --dry-run=client -o yaml | kubectl apply -f -

echo "Kubernetes secret '${K8S_SECRET_NAME}' processed using ${ENV_FILE}."


# --- Kubernetes Deployment Steps ---
echo "Starting Kubernetes deployment to namespace: ${NAMESPACE}..."
# Apply Namespace
echo "Applying Namespace: ${NAMESPACE_FILE}..."
kubectl apply -f "${NAMESPACE_FILE}"

# Apply Backend resources (Ensure YAML uses secretKeyRef: openai-secret)
echo "Applying Backend Deployment: ${BACKEND_DEPLOYMENT_FILE}..."
kubectl apply -f "${BACKEND_DEPLOYMENT_FILE}" -n "${NAMESPACE}"

echo "Applying Backend Service: ${BACKEND_SERVICE_FILE}..."
kubectl apply -f "${BACKEND_SERVICE_FILE}" -n "${NAMESPACE}"

# Apply Frontend resources
echo "Applying Frontend Deployment: ${FRONTEND_DEPLOYMENT_FILE}..."
kubectl apply -f "${FRONTEND_DEPLOYMENT_FILE}" -n "${NAMESPACE}"

echo "Applying Frontend Service: ${FRONTEND_SERVICE_FILE}..."
kubectl apply -f "${FRONTEND_SERVICE_FILE}" -n "${NAMESPACE}"



# --- Completion ---
echo "----------------------------------------"
echo "GKE Cluster setup, Image Push, and Kubernetes deployment applied successfully!"
echo "----------------------------------------"
echo "You can check the status using:"
echo "kubectl get pods,services,deployments -n ${NAMESPACE}"
echo "Wait for LoadBalancer IP: kubectl get service ai-govbot-frontend-service -n ${NAMESPACE} --watch"

# Unset verbose command printing
set +x