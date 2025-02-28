* Build GCP connection to store generated outputs
* At start of the pipeline, add a data download script, unzip script and use data_extract_combine.py to generate the file in merged_input. - DONE
* Use the SaveFile class from save_file.py to reduce duplication of code to save file. Currently was causing import errors for Airflow.
* Develop unittests for each of the Python files defined
* Add dvc and set it to push to Gcloud
* Add logging, tracking and schema generation. - LOGGER ADDED
* Anomaly detection.
* paralellize generate-embedding task




** Refactoring TODOS **

* Try to use xcom for variables - DONE (was previously done based on airflow.py)
* Reduce Embedding task runtime(use smaller models, etc)
