This guide provides detailed instructions for configuring the RAG pipeline through the config.json file.

## Overview

The `config.json` file in the main directory controls the behavior of the RAG pipeline, including:
- Document retrieval parameters
- LLM selection and settings
- Embedding model configuration
- File paths for indexes and data
- MLflow tracking settings
- GCS storage settings
- Moderation controls
- Langfuse observability settings

## Required Configuration Sections

### Paths

Configure where your index directory and document data are stored:

```json
"paths": {
  "index_dir": "src/index",
  "data_path": "src/index/Documents_segments_merged.csv"
}
```

### LLM Configuration

The config supports multiple LLM providers with their own configuration blocks:

```json
"llm": {
  "client": "openai"
},
"openai": {
  "client": "openai",
  "model_name": "gpt-4o-mini",
  "api_key": "sk-xxx"
},
"claude": {
  "client": "claude",
  "model_name": "claude-3-7-sonnet-latest", 
  "api_key": "sk-ant-yourkey"
},
"huggingface": {
  "client": "huggingface",
  "model_name": "deepseek-ai/DeepSeek-R1"
},
"ollama_local": {
  "client": "ollama_local",
  "model_name": "gemma3:4b"
},
"novita": {
  "provider": "novita",
  "token": "Hf_xxx"
}
```

The main `llm` block determines which provider configuration is active.

### Embedding Model

Configure the embedding model to create vector representations:

```json
"embedding": {
  "model": "sentence-transformers/all-mpnet-base-v2"
}
```

### Retriever Settings

Control how documents are retrieved:

```json
"retriever_args": {
  "score_threshold": 1.2,
  "n_docs": 3
}
```

Parameters:
- `score_threshold`: Maximum distance/score threshold for document selection
- `n_docs`: Number of documents to retrieve per query

### GCS Storage Configuration

Configure Google Cloud Storage for index storage:

```json
"gcs_storage": {
  "bucket_name": "datasets-mlops-25",
  "pkl_blob_prefix": "faiss_index/index.pkl",
  "faiss_blob_prefix": "faiss_index/index.faiss",
  "pkl_local_destination": "src/index/index.pkl",
  "faiss_local_destination": "src/index/index.faiss"
}
```

### MLflow Settings

Configure experiment tracking:

```json
"mlflow": {
  "tracking_uri": "http://localhost:8001",
  "experiment_name": "RAG_Pipeline_Experiment"
}
```

### Moderation Settings

Configure content moderation:

```json
"moderation": {
  "enabled": true,
  "sensitivity_level": "medium",
  "input_check": true,
  "output_check": true,
  "log_flagged": true
}
```

### Langfuse Observability

Configure Langfuse for LLM observability:

```json
"langfuse": {
  "secret_key": "sk-xxx",
  "public_key": "pk-xxx",
  "host": "https://us.cloud.langfuse.com"
}
```

## Complete Example

Here's a complete example of the config.json file:

```json
{
    "retriever_args": {
        "score_threshold": 1.2,
        "n_docs": 3  
    },
    "gcs_storage": {
        "bucket_name": "datasets-mlops-25",
        "pkl_blob_prefix": "faiss_index/index.pkl",
        "faiss_blob_prefix": "faiss_index/index.faiss",
        "pkl_local_destination": "src/index/index.pkl",
        "faiss_local_destination": "src/index/index.faiss"
    },
    "novita": {
        "provider": "novita",
        "token": "Hf_xxx"
    },
    "embedding": {
        "model": "sentence-transformers/all-mpnet-base-v2"
    },
    "paths": {
        "index_dir": "src/index",
        "data_path": "src/index/Documents_segments_merged.csv"
    },
    "mlflow": {
        "tracking_uri": "http://localhost:8001",
        "experiment_name": "RAG_Pipeline_Experiment"
    },
    "llm": {
        "client": "openai"
    },
    "openai": {
        "client": "openai",
        "model_name": "gpt-4o-mini",
        "api_key": "sk-xxx"
    },
    "moderation": {
        "enabled": true,
        "sensitivity_level": "medium",
        "input_check": true,
        "output_check": true,
        "log_flagged": true
    },
    "langfuse": {
        "secret_key": "sk-xxx",
        "public_key": "pk-xxx",
        "host": "https://us.cloud.langfuse.com"
    }
}
```

## How to Apply Changes

After modifying the `config.json` file:
1. Save the file
2. Restart the RAG service if it's running
3. Changes will be automatically loaded by the configuration system when the application starts