import tensorflow_data_validation as tfdv
import pandas as pd
import os

def validate_downloaded_data_files(file_schema_pairs):
    """Validate multiple data files against their corresponding schema and return a result dictionary."""
    
    anomalies_found = []

    for file, schema_path in file_schema_pairs:
        # Check if both file and schema exist
        if not os.path.exists(file):
            anomalies_found.append(f"File not found: {file}")
            continue
        if not os.path.exists(schema_path):
            anomalies_found.append(f"Schema file not found: {schema_path}")
            continue

        print(f"Validating file: {file} against schema: {schema_path}")

        try:
            # Load the dataset
            df = pd.read_csv(file)

            if df.empty:
                anomalies_found.append({"file": file, "error": "CSV file is empty"})
                continue

            # Generate statistics for the new data
            stats = tfdv.generate_statistics_from_dataframe(df)

            # Load the stored schema
            schema = tfdv.load_schema_text(schema_path)

            # Validate the new data against the schema
            anomalies = tfdv.validate_statistics(stats, schema)

            if anomalies.anomaly_info:
                for feature, info in anomalies.anomaly_info.items():
                    anomalies_found.append({
                        "file": file, 
                        "feature": feature, 
                        "description": info.description
                    })
        except pd.errors.EmptyDataError:
            anomalies_found.append({"file": file, "error": "CSV is empty or unreadable"})
        except Exception as e:
            anomalies_found.append({"file": file, "error": str(e)})

    # If any anomalies are found, return failure
    if anomalies_found:
        return {"result": False, "anomalies": anomalies_found}

    return {"result": True, "anomalies": []}


# Check validation result and store anomalies in XCom
def check_validation_status(**kwargs):
    ti = kwargs['ti']
    result = ti.xcom_pull(task_ids='validate_schema_task')
    
    if not result["result"]:  # If validation failed
        anomalies = result['anomalies']
        formatted_anomalies = "<br>".join(anomalies)  # Convert list to HTML format
        ti.xcom_push(key='anomalies', value=formatted_anomalies)  # Store anomalies for email
        raise ValueError(f"Schema validation failed: {result['anomalies']}")

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
