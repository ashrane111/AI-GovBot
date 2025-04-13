## How to deploy:


### GCLOUD CLI Setup
- Use the following google link - [GCLOUD CLI SETUP](https://cloud.google.com/sdk/docs/initializing) to intialize GCLOUD locally and select the project ID you want to use.
- Ensure your VM Compute instances API is enabled.

### Script Setup - Linux Terminal
1. In the configuration part of `setup_airflow_vm.sh`, configure the `PROJECT_ID` with the project ID chosen and set the zone `ZONE` as per requirement.
2. Create a google service account key 
    - Create a service account in your Google Cloud project and download the JSON key file.
    - Rename the key file to `google_cloud_key.json`.
    - Save it in the current directory `deployment_scripts/data-pipeline-deployment`
3. Create a .env file in `deployment_scripts/data-pipeline-deployment` using the following parameters:
```bash
AIRFLOW_UID=1000
GOOGLE_APPLICATION_CREDENTIALS=/opt/airflow/secrets/google_cloud_key.json
SMTP_EMAIL=<your_email_account_to_send_email_from>
SMTP_PASSWORD=<your_app_code_for_email>
```
4. Enable `setup_airflow_vm.sh` as an executable:
```bash
chmod +x setup_airflow_vm.sh`
```
5. Run the setup file present in `deployment_scripts/data-pipeline-deployment`:
```bash
./setup_airflow_vm.sh`
```
6. After it is complete, you should be able to view the Airflow UI at the printed host address at port 8080. If unable to see the printed statement, go to google console and in VM Instances find airflow-vm. Use the External IP address from that and use the port 8080 to access the Airflow UI.
