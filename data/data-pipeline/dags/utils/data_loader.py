# file to load data from csv file and serialize it
import pandas as pd
import pickle

def load_data(file_path):
    data = pd.read_csv(file_path)
    serialized_data = pickle.dumps(data)
    return serialized_data

def main():
    csv_file = pd.read_csv('merged_input/Documents_segments_merged.csv')
    # Call the method to perform the data extraction and merging
    load_data(csv_file)

if __name__ == "__main__":
    main()