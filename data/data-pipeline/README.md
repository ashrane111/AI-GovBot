
# How to Use Apache Airflow with Docker

This document details the step-by-step process for setting up and running Apache Airflow in a Dockerized environment. The guide is applicable for Linux, macOS, and Windows (using Docker Desktop with WSL). It covers environment preparation, service account key configuration for Google Cloud Platform, database initialization, Docker image build, application startup, and Data Version Control (DVC) integration.

## 1. Environment Setup

Before running Airflow, set up your project directory by creating the required folders and environment file. Run the following commands in your main data-pipeline directory:

```
cd data/data-pipeline
mkdir -p ./dags ./logs ./plugins ./config ./secrets
echo -e "AIRFLOW_UID=$(id -u)" > .env
```

If you encounter a warning indicating that `AIRFLOW_UID` is not set, manually create a `.env` file in the root of your project with the following content:

```
AIRFLOW_UID=50000
```

## 2. Creating a Google Cloud Platform (GCP) Service Account Key

Apache Airflow can utilize Google Cloud services via a service account key. Follow these steps to configure authentication:

- **Create a Service Account:**  
  In your Google Cloud project, create a service account and download the JSON key file.

- **Rename and Place the Key File:**  
  Rename the downloaded key file to `google_cloud_key.json` and place it inside the `data/data-pipeline/secrets/` folder.

- **Configure the Environment Variable:**  
  Update your project’s root `.env` file to include the following line so that Airflow can locate your GCP credentials:

  ```
  GOOGLE_APPLICATION_CREDENTIALS=/opt/airflow/secrets/google_cloud_key.json
  ```

## 3. Initializing Data Version Control (DVC)

DVC helps track large data files and manage dataset versions within your project. Initialize DVC in the root folder with:

```
dvc init
```

## 4. Initializing the Airflow Database

Before starting Airflow, initialize the metadata database. Run the following command in the directory containing your `docker-compose.yaml`:

```
docker compose up airflow-init
```

The initialization process will run database migrations and create the first Airflow user.

## 5. Building the Docker Instance

Generally, the Docker image is built once at the start of your project. Build your custom Airflow image by executing:

```
docker compose build
```

## 6. Starting the Application

After building the Docker image, start all required containers with:

```
docker compose up
```

For any subsequent changes, simply restart the application using the same command.

## 7. Pushing Data with DVC

To maintain version control for your data, add and push the relevant directories. For example, execute the following commands to track merged inputs, embeddings, and the FAISS index:

```
dvc add data/data-pipeline/dags/merged_input
dvc add data/data-pipeline/dags/embeddings
dvc add data/data-pipeline/dags/FAISS_Index
dvc push
```

## 8. Temporary Airflow Credentials

For testing and local development, temporary Airflow credentials have been set. Please note that these should be updated before deploying to a production environment.

- **Username:** airflow2  
- **Password:** airflow2

---

