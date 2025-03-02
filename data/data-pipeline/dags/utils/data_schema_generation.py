import tensorflow_data_validation as tfdv
import pandas as pd
from tensorflow_metadata.proto.v0 import schema_pb2
import os

def generate_data_statistics(input_csv, output_stats_path, output_schema_path):
    """
    Generate statistics and schema for the given dataset using TFDV.

    Args:
        input_csv (str): Path to the input CSV file.
        output_stats_path (str): Path to save generated statistics.
        output_schema_path (str): Path to save the inferred schema.
    """
    # Ensure the input file exists
    if not os.path.exists(input_csv):
        raise FileNotFoundError(f"Input CSV not found: {input_csv}")

    # Ensure output directory exists
    output_dir = os.path.dirname(output_stats_path)
    os.makedirs(output_dir, exist_ok=True)

    print(f"Processing file: {input_csv}")
    
    # Load the dataset
    df = pd.read_csv(input_csv)

    # Convert pandas DataFrame to a TFDV dataset
    stats = tfdv.generate_statistics_from_dataframe(df)

    # Write the statistics to a file
    tfdv.write_stats_text(stats, output_stats_path)

    # Infer schema from the dataset
    schema = tfdv.infer_schema(stats)

    tfdv.write_schema_text(schema, output_schema_path)

    print(f"Data Statistics and Schema saved at:\n{output_stats_path}\n{output_schema_path}")

    return output_stats_path, output_schema_path

def main():
    # Define correct paths
    base_dir = os.path.dirname(os.path.dirname(__file__))  # Go one level up to `data-pipeline/`
    input_csv = os.path.join(base_dir, "merged_input/agora/documents.csv")
    
    output_dir = os.path.join(base_dir, "schema")  # Ensure directory exists
    os.makedirs(output_dir, exist_ok=True)

    output_stats_path = os.path.join(output_dir, "documents_data_stats.txt")
    output_schema_path = os.path.join(output_dir, "documents_data_schema.pbtxt")  # Use .pbtxt format

    try:
        output_stats_path, output_schema_path = generate_data_statistics(input_csv, output_stats_path, output_schema_path)
        print(f"Output files:\nStats: {output_stats_path}\nSchema: {output_schema_path}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
