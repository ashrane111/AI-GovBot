#!/bin/bash
set -euxo pipefail

log() {
  echo "[`date +'%Y-%m-%d %H:%M:%S'`] $@"
}

log "Updating system packages..."
apt update -y

log "Installing git and Docker dependencies..."
apt update -y
apt install -y git apt-transport-https ca-certificates curl gnupg lsb-release software-properties-common

log "Setting up Docker APT repo..."
mkdir -p /usr/share/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] \
https://download.docker.com/linux/debian $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

apt update -y
apt install -y docker-ce docker-ce-cli containerd.io


log "Enabling Docker service..."
systemctl start docker
systemctl enable docker
# usermod -aG docker $USER

log "Cloning the repo..."
git clone https://github.com/ashrane111/AI-GovBot

log "Setting up Airflow folders..."
cd AI-GovBot/data/data-pipeline
mkdir -p ./logs ./plugins ./secrets

log "Moving secrets and env..."
mv ../../../env_temp .env
mv ../../../google_cloud_key.json ./secrets/google_cloud_key.json

log "Bringing up Docker services..."
docker compose up airflow-init | tee airflow-init.log
docker compose build | tee build.log
docker compose up -d | tee up.log

log "Waiting for Airflow Webserver to become healthy..."

for i in {1..20}; do
  if curl --silent --fail http://localhost:8080/health; then
    log "✅ Airflow Webserver is healthy!"
    break
  else
    log "⏳ Waiting for Airflow... ($i)"
    sleep 10
  fi
done


log "Unpausing DAG: Data_pipeline_HARVEY"
docker compose exec airflow-webserver airflow dags unpause Data_pipeline_HARVEY

log "Triggering DAG: Data_pipeline_HARVEY"
docker compose exec airflow-webserver airflow dags trigger Data_pipeline_HARVEY


log "✅ DONE"
