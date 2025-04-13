#!/bin/bash
set -euo pipefail
set -x

# === CONFIGURATION ===
PROJECT_ID="data-pipeline-deployment-trial"
ZONE="us-east1-d"
VM_NAME="airflow-vm"
MACHINE_TYPE="e2-standard-4"
DISK_SIZE="50GB"
IMAGE_FAMILY="debian-11"
IMAGE_PROJECT="debian-cloud"
TAG="airflow-server"

SSH_KEY_NAME="gcp_airflow_key"
USERNAME=$(whoami)
ENV_FILE=".env"
SECRET_FILE="google_cloud_key.json"
VM_SCRIPT="vm_startup_script.sh"

# === 0. Create passwordless SSH key (only once) ===
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

# === 1. Create the VM ===
gcloud compute instances create "$VM_NAME" \
  --project="$PROJECT_ID" \
  --zone="$ZONE" \
  --machine-type="$MACHINE_TYPE" \
  --boot-disk-size="$DISK_SIZE" \
  --boot-disk-type=pd-balanced \
  --image-family="$IMAGE_FAMILY" \
  --image-project="$IMAGE_PROJECT" \
  --tags="$TAG"

# === 2. Wait for VM boot ===
echo "⏳ Waiting for instance to initialize..."
sleep 40

# === 3. Copy necessary files to VM ===
gcloud compute scp "$ENV_FILE" "$VM_NAME":~/env_temp \
  --zone="$ZONE" --ssh-key-file=~/.ssh/${SSH_KEY_NAME}
gcloud compute scp "$SECRET_FILE" "$VM_NAME":~/google_cloud_key.json \
  --zone="$ZONE" --ssh-key-file=~/.ssh/${SSH_KEY_NAME}
gcloud compute scp "$VM_SCRIPT" "$VM_NAME":~/start.sh \
  --zone="$ZONE" --ssh-key-file=~/.ssh/${SSH_KEY_NAME}

# === 4. Run the setup script inside the VM (with SSH keep-alive) ===
gcloud compute ssh "$VM_NAME" \
  --zone="$ZONE" \
  --ssh-key-file=~/.ssh/${SSH_KEY_NAME} \
  -- -o ServerAliveInterval=30 -o ServerAliveCountMax=10 << EOF
chmod +x ~/start.sh && sudo bash ~/start.sh
EOF

# === 5. Create firewall rule for port 8080 if not exists ===
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

# === 6. Get External IP (with retry) ===
echo "Waiting for external IP assignment..."
for i in {1..10}; do
  EXTERNAL_IP=$(gcloud compute instances describe "$VM_NAME" \
    --zone="$ZONE" \
    --format='get(networkInterfaces[0].accessConfigs[0].natIP)')

  if [[ -n "$EXTERNAL_IP" ]]; then
    break
  else
    echo "⏳ External IP not ready, retrying in 5s..."
    sleep 5
  fi
done

# === 7. Done ===
echo
echo "🎉 Airflow VM deployment complete!"
echo "🌐 Access Airflow UI at: http://$EXTERNAL_IP:8080"
echo "✅ DAG 'Data_pipeline_HARVEY' has been triggered (assuming unpaused)."