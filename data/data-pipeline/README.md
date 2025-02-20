## How to use Airflow
We will be using the dockerized version of Airflow. For windows, Docker Desktop will be required with work in WSL.
For Mac and Linux, docker should be self-explanatory.


### Setting up the environment

For linux (even WSL), will need to run this in the main data-pipeline directory. Assume the same for Mac.
```bash
mkdir -p ./dags ./logs ./plugins ./config
echo -e "AIRFLOW_UID=$(id -u)" > .env
```

If "warning that AIRFLOW_UID is not set" then create a .env file manually with the following.
```bash
AIRFLOW_UID=50000
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


### Temp Credentials for airflow

I have currently set the login and password as the following :-
 
username: airflow2
password: airflow2