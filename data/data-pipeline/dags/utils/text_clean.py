# text cleaning file
import pandas as pd
import re
import pickle
import os
# from save_file import SaveFile

output_dir_name = "merged_input"
clean_data_path = 'Documents_segments_merged.csv'
clean_data_xlsx_path = 'Documents_segments_merged.xlsx'


def clean_text(text):
    text = re.sub(r'\s+', ' ', text)  # Remove extra whitespace
    text = re.sub(r'[^a-zA-Z0-9.,;()\-\s]', '', text)  # Keep only relevant characters
    text = text.lower().strip()
    return text

def clean_full_text(data):
    pd_csv_file = pickle.loads(data)
    # if(pd_csv_file == None):
    #     raise Exception("No file provided")
    
    # if(not isinstance(pd_csv_file, pd.DataFrame)):
    #     raise Exception("Invalid file type. Please provide a pandas DataFrame")
    # Remove 'Tags' column
    if 'Tags' in pd_csv_file.columns:
        pd_csv_file.drop(columns=['Tags'], inplace=True)
    
    # Fill missing values in 'Summary' with "NA"
    if 'Full Text Summary' in pd_csv_file.columns:
        pd_csv_file['Full Text Summary'].fillna("NA", inplace=True)

    pd_csv_file['cleaned_text'] = pd_csv_file['Full Text'].apply(clean_text)

    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), output_dir_name)
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, clean_data_path)
    output_xlsx_path = os.path.join(output_dir, clean_data_xlsx_path)
    pd_csv_file.to_csv(output_path, index=False)    #TODO: upload to gcp in real scenario instead of saving in local
    pd_csv_file.to_excel(output_xlsx_path, index=False)

    # save_data = SaveFile(output_dir, clean_data_path, pd_csv_file)
    # save_data.save_csv_file()
    
    serialized_data = pickle.dumps(pd_csv_file)
    return serialized_data


def main():
    csv_file = pd.read_csv('dags/merged_input/Documents_segments_merged.csv')
    # Call the method to perform the data extraction and merging
    serialized_input_data = pickle.dumps(csv_file)
    clean_full_text(serialized_input_data)

if __name__ == "__main__":
    main()