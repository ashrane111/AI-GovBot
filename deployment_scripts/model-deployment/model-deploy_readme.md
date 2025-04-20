## How to deploy:


### Setup
1.  **Google Cloud SDK (`gcloud`)**: Provides command-line tools for interacting with Google Cloud.
    * Installation Guide: [https://cloud.google.com/sdk/docs/install](https://cloud.google.com/sdk/docs/install)
    * Verify installation: `gcloud --version`
2.  **Ensure Docker Engine is running**: If your OS uses a docker engine based runtime, ensure its running before running the script.
3.  **`kubectl`**: The Kubernetes command-line tool.
    * Installation Guide (often included with `gcloud`): [https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/](https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/) (adjust OS as needed)
    * Install via gcloud: `gcloud components install kubectl`
    * Verify installation: `kubectl version --client`
4.  **Install gke-gcloud-auth-plugin**: run `gcloud components install gke-gcloud-auth-plugin`
5.  **Docker & `buildx`**: Docker Desktop/Engine installed, running, and `buildx` available.
6.  **GCP Account & Permissions**: Access to a GCP project with Billing enabled and necessary permissions (Kubernetes Engine Admin, Artifact Registry Admin, etc.).
7.  **API Key**: Create a `.env` file in the root directory and save the following in it -
```
HUGGINGFACE_KEY=<if hugging face tokens are available>
OPENAI_API_KEY=<your Open AI Key>
ANTHROPIC_API_KEY=<your Anthropic Key>
GOOGLE_APPLICATION_CREDENTIALS=google_cloud_key.json
LANGFUSE_SECRET_KEY=<Langfuse Secret Key>
LANGFUSE_PUBLIC_KEY=<Langfuse Public Key>
LANGFUSE_HOST=<Langfuse host>
```
8.  **GCP Credentials**: Save your service account credentials in `google_cloud_key.json` and save it in the root directory.
9.  **Install jq for bash requirement**: Install jq to process json in bash:
```bash
sudo apt install jq
```


## Configuration

The script uses environment variables defined at the top for configuration (Project ID, Zone, Cluster Name, etc.).

* **Review Defaults:** Open the `model-deploy.sh` script in the deployment_scripts/model-deployment folder  and review the variables in the "Configuration" section. Adjust them if your desired setup differs from the defaults (e.g., different `ZONE`, `CLUSTER_NAME`).
* **Kubernetes Manifest Paths:** Ensure the paths to your `.yaml` files (`NAMESPACE_FILE`, `*_DEPLOYMENT_FILE`, `*_SERVICE_FILE`) within the script match their actual locations in your project.
* **Dockerfile Paths:** Ensure the `BACKEND_DOCKERFILE` and `FRONTEND_DOCKERFILE` variables point to the correct files.
* **K8s Deployment Image Tag:** The script builds/pushes `:latest`. Ensure your Kubernetes Deployment YAMLs (`deployment_scripts/model-deployment/.../k8s-deployment.yaml`) reference the image with the `:latest` tag.
* **K8s Secret Reference:** Ensure your backend deployment YAML (`deployment_scripts/model-deployment/backend/k8s-deployment.yaml`) is configured to use `secretKeyRef` pointing to `openai-secret` for the `OPENAI_API_KEY` environment variable.

## Running the Deployment Script

1.  **Navigate to Model Deployment Directory:** Open your terminal in the model deployment directory:
```bash
cd AI-GovBot/deployment_scripts/model-deployment/
```
2.  **Make Script Executable:** Run (only needed once).
```bash
chmod +x model-deploy.sh
```  
3.  **Execute Script:** Run the script:
```bash
./model-deploy.sh
```
(if asked to type Y for anything, please do so)

4.  **To access the link to the app**: The script will inform about a command that can be used to get the IP address which can be opened. Type the following and wait till external ip pops up:
```bash
kubectl get service ai-govbot-frontend-service -n mlscopers --watch
```

It will look something like this -
```
NAME                         TYPE           CLUSTER-IP       EXTERNAL-IP     PORT(S)        AGE
ai-govbot-frontend-service   LoadBalancer   34.118.230.195   35.229.66.170   80:32639/TCP   69m
```

**What the Scripts Do:**

The script performs the following actions sequentially:

1.  Checks for prerequisite commands (`gcloud`, `kubectl`, `docker`).
2.  Enables necessary GCP APIs.
3.  Creates the GKE cluster (if it doesn't already exist).
4.  Configures `kubectl` to connect to the cluster.
5.  Creates the GAR repository (if it doesn't already exist).
6.  Configures Docker authentication for GAR.
7.  Rotates image tags in GAR (`latest` -> `v1`, `v1` -> `v2`, deletes old `v2`).
8.  Builds multi-architecture backend and frontend images using `docker buildx`.
9.  Pushes the new images tagged as `:latest` to GAR.
10. Securely creates/updates the `openai-secret` Kubernetes secret.
11. Applies all necessary Kubernetes manifests (Namespace, Deployments, Services) using `kubectl apply`.
12. Verifies deployment rollout status.

## Verification

After the script completes successfully:

1.  **Check Pods, Services, Deployments:**
    ```bash
    kubectl get pods,services,deployments -n mlscopers
    ```
    Wait for Pods to reach `Running` status.
2.  **Get Frontend IP:**
    ```bash
    kubectl get service ai-govbot-frontend-service -n mlscopers
    ```
    Note the `EXTERNAL-IP`. It might take a few minutes to appear.
3.  **Access Application:** Open `http://<EXTERNAL_IP>` in your browser.

## Rollback

If the `latest` deployment causes issues, you can manually roll back by:

1.  Editing the `image:` tag in the relevant Kubernetes deployment YAML (`deployment_scripts/.../k8s-deployment.yaml`) to point to the `:v1` tag (which represents the previous version).
2.  Re-applying the modified deployment: `kubectl apply -f <path-to-deployment-yaml> -n mlscopers`.

## Cleanup

To remove the resources created by the script:

1.  **Delete Kubernetes Resources:**
    ```bash
    kubectl delete ns mlscopers # Deletes the namespace and everything in it
    # Or delete individual components if needed
    ```
2.  **Delete GKE Cluster:**
    ```bash
    gcloud container clusters delete ${CLUSTER_NAME} --zone=${ZONE} --project=${PROJECT_ID} --quiet
    ```
3.  **Delete GAR Repository:**
    ```bash
    gcloud artifacts repositories delete ${GAR_REPOSITORY_NAME} --location=${REGION} --project=${PROJECT_ID} --quiet
    ```