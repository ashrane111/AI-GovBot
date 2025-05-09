import pandas as pd
import os
import logging

# Set up custom logger instead of root logger
logger = logging.getLogger('data_extract_combine_logger')
logger.setLevel(logging.INFO)

# Create directory for logs if it doesn't exist
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'util_logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'data_extract_combine.log')

# Create file handler and set formatter
handler = logging.FileHandler(log_file)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# Add handler to logger
logger.addHandler(handler)

# Prevent log propagation to Airflow's root logger
logger.propagate = False

def make_input_dir():
    path = 'merged_input'
    try:
        os.makedirs(path)
    except FileExistsError:
        pass


def extract_and_merge_documents(temp_dir=""):
    try:
        make_input_dir()
        documents_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), temp_dir)
        
        documents = pd.read_csv(f"{documents_dir}/documents.csv")
        logger.info("Accessed documents.csv")
        
        segments = pd.read_csv(f"{documents_dir}/segments.csv")
        logger.info("Accessed segments.csv")

        authorities = pd.read_csv(f"{documents_dir}/authorities.csv")
        logger.info("Accessed authorities.csv")

        authorities_extract = authorities[['Name', 'Jurisdiction']]
        logger.info("Extracted Name and Jurisdiction from authorities")

        # Fill empty Jurisdiction values in authorities with "Other"
        authorities_extract = authorities[['Name', 'Jurisdiction']]
        authorities_extract.loc[:, 'Jurisdiction'] = authorities_extract['Jurisdiction'].fillna('Other')
        authorities_extract.loc[authorities_extract['Jurisdiction'] == '', 'Jurisdiction'] = 'Other'


        segments_result = segments.groupby('Document ID').agg(lambda x: ', '.join(x.astype(str))).reset_index()
        segments_required = segments_result[['Document ID', 'Text', 'Summary']]
        segments_required = segments_required.rename(columns={'Text': 'Full Text', 'Summary': 'Full Text Summary'})
        logger.info("Extracted necessary columns from segments")

        documents_extracted = documents[['AGORA ID', 'Official name', 'Casual name', 'Link to document',
                                         'Authority', 'Collections', 'Most recent activity',
                                         'Most recent activity date', 'Proposed date', 'Primarily applies to the government',
                                         'Primarily applies to the private sector', 'Short summary',
                                         'Long summary']]
        logger.info("Extracted necessary columns from documents")

        documents_with_jurisdiction = pd.merge(
            documents_extracted,
            authorities_extract,
            left_on='Authority',
            right_on='Name',
            how='left'
        )
        logger.info("Merged documents with authorities to get Jurisdiction")

        # Drop the duplicate Name column (from authorities) if you don't need it
        if 'Name' in documents_with_jurisdiction.columns:
            documents_with_jurisdiction = documents_with_jurisdiction.drop('Name', axis=1)


        merged_document_segments = pd.merge(
            documents_with_jurisdiction,
            segments_required,
            left_on='AGORA ID',
            right_on='Document ID',
            how='left'  # Using left join to keep all documents
        ).drop('Document ID', axis=1)
        logger.info("Merged documents and segments using left join")

        # Check for missing Full Text and replace with Long summary
        missing_full_text_mask = merged_document_segments['Full Text'].isna() | (merged_document_segments['Full Text'] == '')
        missing_count = missing_full_text_mask.sum()
        logger.info(f"Found {missing_count} documents with missing Full Text. Using Long summary as fallback.")

        merged_document_segments.loc[missing_full_text_mask, 'Full Text'] = merged_document_segments.loc[missing_full_text_mask, 'Long summary']

        save_file_name = 'Documents_segments_merged'
        output_csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), f'merged_input/{save_file_name}.csv')
        output_xlsx_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), f'merged_input/{save_file_name}.xlsx')
        
        merged_document_segments.to_csv(output_csv_path, index=False)
        logger.info(f"Saved merged data to {save_file_name}.csv")
        
        merged_document_segments.to_excel(output_xlsx_path, index=False)
        logger.info(f"Saved merged data to {save_file_name}.xlsx")
        
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise

def main():
    temp_dir = "merged_input/agora"
    try:
        extract_and_merge_documents(temp_dir)
    except Exception as e:
        logger.error(f"Error in main: {e}")
        print(e)

if __name__ == "__main__":
    main()