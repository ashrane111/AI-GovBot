## How to use Airflow

We will be using the dockerized version of Airflow. For windows, Docker Desktop will be required with work in WSL.
For Linux, docker should be self-explanatory. M-architecture macs might have issues with Tensorflow.


### Setting up the environment

For linux (even WSL), will need to run this in the main data-pipeline directory. Assume the same for Mac.
```bash
cd data/data-pipeline
mkdir -p ./logs ./plugins ./secrets
echo -e "AIRFLOW_UID=$(id -u)" > .env
```

If "warning that AIRFLOW_UID is not set" then create a .env file manually with the following for windows.
```bash
AIRFLOW_UID=50000
```

### Create a GCP key 

- Create a service account in your Google Cloud project and download the JSON key file.

- Rename the key file to `google_cloud_key.json`.

- Place the key inside the `data/data-pipeline/secrets/` folder.

### Set up .env file
A .env file should be present from the previous steps. If not, create one on the same level as the data-pipeline folder. 
```bash
AIRFLOW_UID=1000
GOOGLE_APPLICATION_CREDENTIALS=/opt/airflow/secrets/google_cloud_key.json
SMTP_EMAIL=<your_email_account_to_send_email_from>
SMTP_PASSWORD=<your_app_code_for_email>
```
To get App Code, follow the instruction provided here: [Get App Code](https://support.google.com/accounts/answer/185833) and get your smtp password.

### Set up config.json
In data/data-pipeline/config/, edit config.json to add your own email id, SentenceTransformer embedding model and owner name. This email will be used to receive the data.



### Initialize Data Version Control (DVC)
Run the following command in the root folder.

```bash
dvc init
```

### Initialize the database

Run the following docker command in the same directory where the docker-compose.yaml is present.

```bash
docker compose up airflow-init
```

### Build the docker instance

Usually you need to do this once at start.

```bash
docker compose build
```

### Start the application

The following is the command is to start the application :-

```bash
docker compose up
```

After every changes, can restart using this.

### DVC Push

- Use version control on the the data.

```bash
dvc add data/data-pipeline/dags/merged_input
dvc add data/data-pipeline/dags/embeddings
dvc add data/data-pipeline/dags/FAISS_Index
dvc push
```

### Temp Credentials for airflow

I have currently set the login and password as the following :-
 
username: airflow2
password: airflow2