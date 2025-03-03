import pandas as pd
import os

# List your CSV file paths
csv_files = ["authorities.csv", "collections.csv", "documents.csv", "segments.csv"]



# Load and concatenate
df_list = [pd.read_csv(os.path.join(os.path.dirname(os.path.dirname(__file__)), f'merged_input/agora/{file}')) for file in csv_files]
df = pd.concat(df_list, ignore_index=True)

# Save merged file
output_csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), f'merged_input/merged_data.csv')
df.to_csv(output_csv_path, index=False)
print("Merged dataset saved as merged_data.csv")

# Print all available column names
print("Columns in the dataset:\n", df.columns.tolist())
