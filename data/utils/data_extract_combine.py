import pandas as pd
import os



def make_input_dir():
    path = 'merged_input'

    try:
        os.makedirs(path)
    except FileExistsError:
        pass
        

def extract_and_merge_documents(temp_dir = ""):
    make_input_dir()
    documents = pd.read_csv(f"{temp_dir}/documents.csv")
    print("Accessed documents.csv")
    segments = pd.read_csv(f"{temp_dir}/segments.csv")
    print("Accessed segments.csv")

    segments_result = segments.groupby('Document ID').agg(lambda x: ', '.join(x.astype(str))).reset_index()

    segments_required = segments_result[['Document ID', 'Text', 'Summary']]
    segments_required = segments_required.rename(columns={'Text': 'Full Text', 'Summary': 'Full Text Summary'})
    
    print("Extracted necessary columns from segments")

    documents_extracted = documents[['AGORA ID', 'Official name', 'Casual name', 'Link to document',
       'Authority', 'Collections', 'Most recent activity',
       'Most recent activity date', 'Proposed date', 'Primarily applies to the government',
       'Primarily applies to the private sector', 'Short summary',
       'Long summary', 'Tags']]
    
    print("Extracted necessary columns from documents")

    merged_document_segments = pd.merge(
        documents_extracted,
        segments_required,
        left_on='AGORA ID',
        right_on='Document ID'
    ).drop('Document ID', axis=1)
    
    print("Merged documents and segments")
    
    save_file_name = 'Documents_segments_merged'

    merged_document_segments.to_csv(f'merged_input/{save_file_name}.csv', index=False)
    print(f"Saved merged data to {save_file_name}.csv")
    merged_document_segments.to_excel(f'merged_input/{save_file_name}.xlsx', index=False)
    print(f"Saved merged data to {save_file_name}.xlsx")



def main():
    temp_dir = "../agora"
    # Call the method to perform the data extraction and merging
    extract_and_merge_documents(temp_dir)

if __name__ == "__main__":
    main()