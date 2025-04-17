# Ensure environment variables are set correctly first
export PROJECT_ID="data-pipeline-deployment-trial"
export ZONE="us-east1-d"
export CLUSTER_NAME="ai-govbot-cluster" # Or ai-govbot-cluster-zonal

# Carefully copy and run this multi-line command
gcloud container clusters create ${CLUSTER_NAME} \
    --zone=${ZONE} \
    --num-nodes=1 \
    --machine-type=e2-standard-4 \
    --disk-type=pd-standard \
    --scopes="https://www.googleapis.com/auth/cloud-platform"


# export PROJECT_ID="data-pipeline-deployment-trial"
# export ZONE="us-east1-d"
# export CLUSTER_NAME="ai-govbot-cluster"

# gcloud container clusters get-credentials ${CLUSTER_NAME} --zone=${ZONE} --project=${PROJECT_ID}