# Data Pipeline Workflow Overview

This document provides a detailed overview of the data pipeline workflow implemented using Apache Airflow. The pipeline is designed to take raw data from external sources through a series of structured processing stages—from data acquisition and validation to data transformation, feature engineering, indexing, and finally uploading to a cloud storage endpoint. Each stage is encapsulated in an Airflow task, ensuring modular, reproducible, and easily maintainable code.

## Data-pipeline Directory Structure

```
│
├── Dockerfile                     # Defines Airflow container with dependencies
├── docker-compose.yaml            # Orchestrates Airflow services
├── requirements.txt               # Python package dependencies
├── .env                           # Environment variables and credentials
│
├── dags/                          # Airflow DAG definitions
│   ├── airflow.py                 # Main DAG defining the data pipeline workflow
│   │
│   └── utils/                     # Utility functions for pipeline tasks
│       ├── create_vector_index.py # Creates FAISS vector index from embeddings
│       ├── data_extract_combine.py# Extracts and merges document data
│       ├── data_loader.py         # Loads and prepares data for processing
│       ├── data_validation.py     # Validates data against defined schemas
│       ├── download_data.py       # Downloads and extracts source data files
│       ├── embeddings_gen.py      # Generates text embeddings using transformers
│       ├── gcs_upload.py          # Uploads processed data to Google Cloud Storage
│       ├── preprocess_data.py     # Preprocesses text data for embedding
│       └── text_clean.py          # Cleans and normalizes text content
│
├── config/                        # Configuration files
│   └── config.json                # Central configuration for pipeline parameters
│
├── merged_input/                  # Storage for downloaded and processed data
│   └── agora/                     # Directory containing source files
│
├── schema/                        # Schema definitions for data validation
│   ├── authorities_data_schema.pbtxt
│   ├── collections_data_schema.pbtxt
│   ├── documents_data_schema.pbtxt
│   └── segments_data_schema.pbtxt
│
├── FAISS_Index/                   # Output directory for vector indices
│   └── legal_embeddings.index     # Generated vector index file
│
└── embeddings/                    # Storage for generated embeddings
    └── embeddings.pkl             # Serialized text embeddings
```

## Workflow Overview

Below is the graphical representation of the pipeline




## Pipeline Stages

### 1. Data Acquisition
- **Task:** `download_unzip_task`
- **Description:**  
  This task initiates the pipeline by downloading a zipped dataset from a specified URL and unzipping it into a designated directory (`merged_input`). It ensures that the data acquisition process is reproducible, and external dependencies (such as network access) are well defined.

### 2. Schema Validation
- **Task:** `validate_schema_task`
- **Description:**  
  Once the data is downloaded, the pipeline validates the integrity and structure of the CSV files. The task pairs each data file (like `authorities.csv`, `collections.csv`, `documents.csv`, and `segments.csv`) with its expected schema (stored in corresponding `.pbtxt` files). This stage is essential to ensure data quality and consistency before any processing occurs.

### 3. Validation Check
- **Task:** `check_validation_task`
- **Description:**  
  This task checks the output from the schema validation process. It identifies any anomalies such as schema mismatches or missing values. The results are then used to determine whether the pipeline should proceed or trigger an alert.

### 4. Anomaly Alert for Validation Failure
- **Task:** `trigger_validation_failure_email`
- **Description:**  
  Should the validation check detect any anomalies, this task sends an automated email alert detailing the issues. This error-handling mechanism helps in prompt identification and resolution of data quality problems.

### 5. Data Integration
- **Task:** `data_combine_task`
- **Description:**  
  After successful validation, this stage merges and combines various documents from the dataset into a single coherent file (e.g., `Documents_segments_merged.csv`). The custom function `extract_and_merge_documents` achieves this by integrating fragmented data sources.

### 6. Data Loading
- **Task:** `load_data_task`
- **Description:**  
  The unified dataset is then loaded into memory. This prepares the data for further preprocessing and ensures that subsequent tasks can access the complete dataset.

### 7. Data Preprocessing
- **Task:** `preprocess_data_task`
- **Description:**  
  This stage involves cleaning and transforming the loaded data. It prepares the dataset by handling missing values, transforming features, and applying any necessary formatting adjustments. The modular design of the preprocessing code allows for easy customization.

### 8. Text Cleaning
- **Task:** `clean_text_task`
- **Description:**  
  Specialized text cleaning is applied to the preprocessed data. The function `clean_full_text` refines the dataset by removing noise, correcting formatting, and standardizing text—an essential step for natural language processing tasks.

### 9. Embeddings Generation
- **Task:** `generate_embeddings_task`
- **Description:**  
  Once the text is cleaned, this task converts the textual data into numerical embeddings using the `generate_embeddings` function. These embeddings capture semantic meaning and are critical for downstream tasks such as similarity searches or feature extraction.

### 10. Index Creation
- **Task:** `create_index_task`
- **Description:**  
  Using the generated embeddings, the pipeline creates a vector index with the `create_index` function. This index facilitates efficient retrieval operations and can serve as the basis for similarity matching in applications like search or recommendation systems.

### 11. Upload to Cloud Storage
- **Task:** `upload_to_gcs_task`
- **Description:*