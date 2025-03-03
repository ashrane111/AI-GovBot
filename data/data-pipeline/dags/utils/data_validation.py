import os
import pandas as pd
import tensorflow_data_validation as tfdv

def validate_downloaded_data_files(file_schema_pairs):
    """Validate multiple data files against their corresponding schema and return a result dictionary."""
    
    anomalies_found = {}

    for file, schema_path in file_schema_pairs:
        # Initialize anomalies list for this file
        anomalies_found[file] = []

        # Check if both file and schema exist
        if not os.path.exists(file):
            anomalies_found[file].append("File not found")
            continue
        if not os.path.exists(schema_path):
            anomalies_found[file].append("Schema file not found")
            continue

        print(f"Validating file: {file} against schema: {schema_path}")

        try:
            # Load the dataset
            df = pd.read_csv(file)

            if df.empty:
                anomalies_found[file].append("CSV file is empty")
                continue

            # Generate statistics for the new data
            stats = tfdv.generate_statistics_from_dataframe(df)

            # Load the stored schema
            schema = tfdv.load_schema_text(schema_path)

            # Validate the new data against the schema
            anomalies = tfdv.validate_statistics(stats, schema)

            if anomalies.anomaly_info:
                for feature, info in anomalies.anomaly_info.items():
                    anomalies_found[file].append(f"Feature: {feature}, Error: {info.description}")
        except pd.errors.EmptyDataError:
            anomalies_found[file].append("CSV is empty or unreadable")
        except Exception as e:
            anomalies_found[file].append(str(e))

        # Remove files with no anomalies
        if not anomalies_found[file]:
            del anomalies_found[file]

    # If any anomalies are found, return failure
    return {"result": not bool(anomalies_found), "anomalies": anomalies_found}



# Check validation result and store anomalies in XCom
# def check_validation_status(**kwargs):
#     ti = kwargs['ti']
#     result = ti.xcom_pull(task_ids='validate_schema_task')
    
#     if not result["result"]:  # If validation failed
#         anomalies = result['anomalies']
#         formatted_anomalies = "<br>".join([f"File: {a['file']}, Error: {a['error']}" for a in anomalies])
#         ti.xcom_push(key='anomalies', value=formatted_anomalies)  # Store formatted anomalies for email
#         raise ValueError(f"Schema validation failed: {formatted_anomalies}")

def check_validation_status(**kwargs):
    ti = kwargs['ti']
    result = ti.xcom_pull(task_ids='validate_schema_task')
    
    if not result["result"]:  # If validation failed
        anomalies = result['anomalies']  # Dictionary of file -> list of errors
        
        # Convert the structured anomalies into a readable HTML format
        formatted_anomalies = "<br>".join(
            [f"File: {file}<br>" + "<br>".join([f"&nbsp;&nbsp;- {error}" for error in errors])
             for file, errors in anomalies.items()]
        )

        ti.xcom_push(key='anomalies', value=formatted_anomalies)  # Store formatted anomalies for email
        raise ValueError(f"Schema validation failed: {formatted_anomalies}")


# Test the function manually
if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(__file__))

    file_schema_pairs= [
            (os.path.join(base_dir, "merged_input/agora/authorities.csv") ,
             os.path.join(base_dir, "schema/authorities_data_schema.pbtxt")),
            (os.path.join(base_dir, "merged_input/agora/collections.csv"),
             os.path.join(base_dir, "schema/collections_data_schema.pbtxt")),
            (os.path.join(base_dir, "merged_input/agora/documents.csv"),
             os.path.join(base_dir, "schema/documents_data_schema.pbtxt")),
            (os.path.join(base_dir, "merged_input/agora/segments.csv"),
             os.path.join(base_dir, "schema/documents_data_schema.pbtxt")),
        ]
    # schema_path = os.path.join(base_dir, "merged_input/data_schema.txt") 
    # input_csv = os.path.join(base_dir, "merged_input/Documents_segments_merged.csv") 
    # input_csv = os.path.join(base_dir, "merged_input/agora/segments.csv") 


    validation_result = validate_downloaded_data_files(file_schema_pairs)
    print(validation_result)  # Expected: {"result": True/False, "anomalies": [...]}
