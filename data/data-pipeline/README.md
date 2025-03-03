## How to Run the Pipeline

**Recommended Specs**
It would be recommended to run on a system with atleast 16 GB of RAM. Arm architectures might have issues with Tensorflow Data Validation package as they do not support them. Recommended to run on Linux/Windows Docker.

1. **Set Up the Project Repo and Environment:**  
   To start working with the project, please follow the setup instructions outlined in the [Project Setup Guide](./readme/setup.md).

2. **Launch Airflow:**  
   Start Airflow and trigger the DAG to execute the pipeline.

3. **Monitor Logs:**  
   Check the `/logs` folder or the Airflow UI for real-time status and error alerts.

4. **For Unit Tests**
   On your own machine run create a python virtual environment using - [Setup Venv](https://docs.python.org/3/library/venv.html)
   ```bash
   pip install -r requirements.txt
   ``` 
   in the tests folder. Following this run 
   ```bash
   pytest tests/unit/ -v
   ```
   from root directory.

5. **Data Bias Detection Report**
   This can be found in [Bias Report](./readme/Bias_Detection_Report.md)