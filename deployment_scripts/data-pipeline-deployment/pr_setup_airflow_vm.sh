#!/bin/bash
set -euo pipefail
set -x

# === CONFIGURATION ===
PROJECT_ID="${3:-data-pipeline-deployment-trial}"
ZONE="us-east1-d"
REGION="us-east1"
VM_NAME="${1:-airflow-vm}"
BRANCH_NAME="${2:-main}"
STATIC_IP_NAME="$BRANCH_NAME-airflow-access-ip"
MACHINE_TYPE="e2-standard-4"
DISK_SIZE="50GB"
IMAGE_FAMILY="debian-11"
IMAGE_PROJECT="debian-cloud"
TAG="airflow-server"

SSH_KEY_NAME="gcp_airflow_key"
USERNAME=rixirx
ENV_FILE=".env"
SECRET_FILE="google_cloud_key.json"
VM_SCRIPT="pr_vm_startup_script.sh"

# === 0. Create passwordless SSH key if needed ===
if [ ! -f ~/.ssh/${SSH_KEY_NAME} ]; then
  ssh-keygen -t rsa -f ~/.ssh/${SSH_KEY_NAME} -C "airflow_vm" -N ""
fi

# === 0a. Upload SSH key only if not already uploaded ===
if ! gcloud compute os-login ssh-keys list \
  --format="value(key)" | grep -F "$(cat ~/.ssh/${SSH_KEY_NAME}.pub)" &>/dev/null; then
  gcloud compute os-login ssh-keys add --key-file ~/.ssh/${SSH_KEY_NAME}.pub
else
  echo "SSH key already uploaded to OS Login"
fi

# === 1. Reserve a static external IP if not already reserved ===
if ! gcloud compute addresses describe "$STATIC_IP_NAME" --region="$REGION" &>/dev/null; then
  echo "Creating new static IP '$STATIC_IP_NAME'..."
  gcloud compute addresses create "$STATIC_IP_NAME" --region="$REGION"
else
  echo "Static IP '$STATIC_IP_NAME' already reserved."
fi

# === 2. Get the reserved static IP ===
STATIC_IP=$(gcloud compute addresses describe "$STATIC_IP_NAME" \
  --region="$REGION" \
  --format='get(address)')

# === 3. Check if VM instance exists, delete if it does ===
if gcloud compute instances describe "$VM_NAME" --zone="$ZONE" &>/dev/null; then
  echo "VM instance '$VM_NAME' already exists. Deleting it..."
  gcloud compute instances delete "$VM_NAME" --zone="$ZONE" --quiet
  
  echo "Waiting for VM instance deletion to complete..."
  while gcloud compute instances describe "$VM_NAME" --zone="$ZONE" &>/dev/null; do
    echo "Instance still exists, waiting 10 more seconds..."
    sleep 10
  done
  echo "VM instance deletion completed."
  
  # Additional wait to ensure resources are fully released
  sleep 20
fi

# === 4. Create the VM and attach the static IP ===
echo "Creating new VM instance '$VM_NAME'..."
gcloud compute instances create "$VM_NAME" \
  --project="$PROJECT_ID" \
  --zone="$ZONE" \
  --machine-type="$MACHINE_TYPE" \
  --boot-disk-size="$DISK_SIZE" \
  --boot-disk-type=pd-balanced \
  --image-family="$IMAGE_FAMILY" \
  --image-project="$IMAGE_PROJECT" \
  --tags="$TAG" \
  --address="$STATIC_IP" \
  --metadata=branch="$BRANCH_NAME"

# === 5. Wait for VM boot ===
echo "⏳ Waiting for instance to initialize..."
sleep 40

# === 6. Copy necessary files to VM ===
gcloud compute scp "$ENV_FILE" "$VM_NAME":~/env_temp \
  --zone="$ZONE" --ssh-key-file=~/.ssh/${SSH_KEY_NAME}
gcloud compute scp "$SECRET_FILE" "$VM_NAME":~/google_cloud_key.json \
  --zone="$ZONE" --ssh-key-file=~/.ssh/${SSH_KEY_NAME}
gcloud compute scp "$VM_SCRIPT" "$VM_NAME":~/start.sh \
  --zone="$ZONE" --ssh-key-file=~/.ssh/${SSH_KEY_NAME}

# === 7. Run setup script inside VM ===
gcloud compute ssh "$VM_NAME" \
  --zone="$ZONE" \
  --ssh-key-file=~/.ssh/${SSH_KEY_NAME} \
  -- -o ServerAliveInterval=30 -o ServerAliveCountMax=10 << EOF
chmod +x ~/start.sh && sudo bash ~/start.sh
EOF

# === 8. Create firewall rule if not exists ===
if ! gcloud compute firewall-rules list --format="value(name)" | grep -q "^allow-airflow-8080$"; then
  gcloud compute firewall-rules create allow-airflow-8080 \
    --allow tcp:8080 \
    --target-tags="$TAG" \
    --description="Allow Airflow UI on port 8080" \
    --direction=INGRESS \
    --priority=1000 \
    --network=default
else
  echo "Firewall rule 'allow-airflow-8080' already exists."
fi

# === 9. Done ===
echo
echo "🎉 Airflow VM deployment complete!"
echo "🌐 Access Airflow UI at: http://$STATIC_IP:8080"
echo "✅ DAG 'Data_pipeline_HARVEY' has been triggered (assuming unpaused)."
