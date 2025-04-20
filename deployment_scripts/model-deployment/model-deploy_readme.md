## How to deploy:


### Setup
1.  **Google Cloud SDK (`gcloud`)**: Provides command-line tools for interacting with Google Cloud.
    * Installation Guide: [https://cloud.google.com/sdk/docs/install](https://cloud.google.com/sdk/docs/install)
    * Verify installation: `gcloud --version`
2.  **`kubectl`**: The Kubernetes command-line tool.
    * Installation Guide (often included with `gcloud`): [https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/](https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/) (adjust OS as needed)
    * Install via gcloud: `gcloud components install kubectl`
    * Verify installation: `kubectl version --client`
3.  **Docker & `buildx`**: Docker Desktop/Engine installed, running, and `buildx` available.
4.  **GCP Account & Permissions**: Access to a GCP project with Billing enabled and necessary permissions (Kubernetes Engine Admin, Artifact Registry Admin, etc.).
5.  **OpenAI API Key**: Create a `.env` file in the root directory and save your key as `OPENAI_API_KEY`

## Configuration

The script uses environment variables defined at the top for configuration (Project ID, Zone, Cluster Name, etc.).

* **Review Defaults:** Open the `model-deploy.sh` script in the deployment_scripts/model-deployment folder  and review the variables in the "Configuration" section. Adjust them if your desired setup differs from the defaults (e.g., different `ZONE`, `CLUSTER_NAME`).
* **Kubernetes Manifest Paths:** Ensure the paths to your `.yaml` files (`NAMESPACE_FILE`, `*_DEPLOYMENT_FILE`, `*_SERVICE_FILE`) within the script match their actual locations in your project.
* **Dockerfile Paths:** Ensure the `BACKEND_DOCKERFILE` and `FRONTEND_DOCKERFILE` variables point to the correct files.
* **K8s Deployment Image Tag:** The script builds/pushes `:latest`. Ensure your Kubernetes Deployment YAMLs (`deployment_scripts/model-deployment/.../k8s-deployment.yaml`) reference the image with the `:latest` tag.
* **K8s Secret Reference:** Ensure your backend deployment YAML (`deployment_scripts/model-deployment/backend/k8s-deployment.yaml`) is configured to use `secretKeyRef` pointing to `openai-secret` for the `OPENAI_API_KEY` environment variable.

## Running the Deployment Script

1.  **Navigate to Project Root:** Open your terminal in the root directory of the `AI-GovBot` project.
2.  **Make Script Executable:** Run `chmod +x deployment_scripts/model-deployment/model-deploy.sh`  (only needed once).
3.  **Execute Script:** Run the script:
    ```bash
    .deployment_scripts/model-deployment/model-deploy.sh
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