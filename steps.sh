#!/bin/bash

# Exit on error, undefined variable, or pipe failure
set -euo pipefail
# Print commands as they execute (optional, remove '#' to disable)
set -x

# --- Configuration ---
PROJECT_ID="data-pipeline-deployment-trial"
ZONE="us-east1-d"                            # Zone for GKE Cluster
REGION="us-east1"                            # Region for GAR Repository (must contain ZONE)
CLUSTER_NAME="ai-govbot-cluster"       # Name for your GKE cluster
GAR_REPOSITORY_NAME="ai-govbot-repo"         # Name for your GAR repository
NAMESPACE="mlscopers"                        # Kubernetes namespace

# Define Dockerfile paths
BACKEND_DOCKERFILE="deployment_scripts/model-deployment/backend/Dockerfile"
FRONTEND_DOCKERFILE="deployment_scripts/model-deployment/frontend/Dockerfile"

# Define K8s manifest paths
NAMESPACE_FILE="deployment_scripts/model-deployment/k8s-namespace.yaml" # ADJUST PATH IF NEEDED
BACKEND_DEPLOYMENT_FILE="deployment_scripts/model-deployment/backend/k8s-deployment.yaml"
BACKEND_SERVICE_FILE="deployment_scripts/model-deployment/backend/k8s-service.yaml"
FRONTEND_DEPLOYMENT_FILE="deployment_scripts/model-deployment/frontend/k8s-deployment.yaml"
FRONTEND_SERVICE_FILE="deployment_scripts/model-deployment/frontend/k8s-service.yaml"

# Define GAR Image Names (using variables defined above)
BACKEND_IMAGE_NAME="${REGION}-docker.pkg.dev/${PROJECT_ID}/${GAR_REPOSITORY_NAME}/ai-govbot-backend:v1"
FRONTEND_IMAGE_NAME="${REGION}-docker.pkg.dev/${PROJECT_ID}/${GAR_REPOSITORY_NAME}/ai-govbot-frontend:v1"
GAR_REPO_PATH_PREFIX="${REGION}-docker.pkg.dev" # Used for docker login config

# --- GCP Project Setup (Run manually once if needed) ---
# echo "Ensure required APIs are enabled: container, artifactregistry, compute"
# gcloud services enable container.googleapis.com artifactregistry.googleapis.com compute.googleapis.com --project=${PROJECT_ID}
# echo "Ensure gcloud is configured for project ${PROJECT_ID}"
# gcloud config set project ${PROJECT_ID}

# --- Create Zonal GKE Cluster ---
echo "Checking/Creating Zonal GKE cluster ${CLUSTER_NAME} in zone ${ZONE}..."
if ! gcloud container clusters describe ${CLUSTER_NAME} --zone ${ZONE} --project=${PROJECT_ID} &> /dev/null; then
    gcloud container clusters create ${CLUSTER_NAME} \
        --project=${PROJECT_ID} \
        --zone=${ZONE} \
        --num-nodes=1 \
        --machine-type=e2-standard-4 \
        --node-disk-type=pd-standard \
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

# --- Configure Docker for Artifact Registry ---
echo "Configuring Docker credentials for Artifact Registry: ${GAR_REPO_PATH_PREFIX}..."
gcloud auth configure-docker ${GAR_REPO_PATH_PREFIX} --project=${PROJECT_ID}

# --- Build and Push Multi-Arch Images using docker buildx ---
# Note: Ensure buildx is set up if needed: docker buildx create --use
echo "Building and pushing multi-arch backend image to ${BACKEND_IMAGE_NAME}..."
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t ${BACKEND_IMAGE_NAME} \
  -f ${BACKEND_DOCKERFILE} \
  --push \
  . # Build context is current directory (project root)

echo "Building and pushing multi-arch frontend image to ${FRONTEND_IMAGE_NAME}..."
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t ${FRONTEND_IMAGE_NAME} \
  -f ${FRONTEND_DOCKERFILE} \
  --push \
  . # Build context is current directory (project root)

echo "Docker images built and pushed to GAR successfully."
'''
# --- !! MANUAL STEP REQUIRED !! ---
echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
echo "!! IMPORTANT: Manually edit the backend deployment YAML file NOW!      !!"
echo "!! Replace '__API_KEY_PLACEHOLDER__' in:"
echo "!!   ${BACKEND_DEPLOYMENT_FILE}"
echo "!! with your actual OpenAI API key before proceeding."
echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
read -p "Press Enter to continue AFTER editing the file..." -r

# --- Kubernetes Deployment Steps ---
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

# --- Completion ---
echo "----------------------------------------"
echo "GKE Cluster setup, Image Push, and Kubernetes deployment applied successfully!"
echo "----------------------------------------"
echo "You can check the status using:"
echo "kubectl get all -n ${NAMESPACE}"
echo "kubectl get service ai-govbot-frontend-service -n ${NAMESPACE}"
echo "Note: It might take a minute or two for the LoadBalancer IP to become available."
'''
# Unset verbose command printing (if set -x was used)
set +x