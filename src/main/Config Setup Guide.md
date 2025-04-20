This guide provides detailed instructions for configuring the RAG pipeline through the config.json file.

## Overview

The `config.json` file in the main directory controls the behavior of the RAG pipeline, including:
- Document retrieval parameters
- LLM selection and settings
- Embedding model configuration
- File paths for indexes and data
- MLflow tracking settings

## Required Configuration Sections

### Paths

Configure where your vector index and document data are stored:

```json
"paths": {
  "index_file": "path/to/your/faiss/index.faiss",
  "metadata_file": "path/to/your/metadata.pkl",
  "data_file": "path/to/your/data.json"
}
```

Note: Relative paths are automatically resolved relative to the project root.

### LLM Configuration

Select and configure the Large Language Model:

```json
"llm": {
  "client": "openai",  
  "model": "gpt-3.5-turbo", 
  "temperature": 0.3,
  "max_tokens": 500
}
```

Available `client` options:
- `openai` - Requires OpenAI API key in environment variables
- `anthropic` - For Claude models, requires Anthropic API key
- `huggingface` - For Hugging Face models
- `ollama` - For local models via Ollama

### Embedding Model

Configure the embedding model to create vector representations:

```json
"embedding": {
  "model": "sentence-transformers/all-MiniLM-L6-v2"
}
```

Common choices include:
- `sentence-transformers/all-MiniLM-L6-v2` (default)
- `sentence-transformers/all-mpnet-base-v2` (higher quality)
- `openai` embedding models (requires separate configuration)

### Retriever Settings

Control how documents are retrieved:

```json
"retriever_args": {
  "top_k": 5,
  "similarity_threshold": 0.7
}
```

Parameters:
- `top_k`: Number of documents to retrieve per query
- `similarity_threshold`: Minimum similarity score (0-1) for inclusion

### MLflow Settings

Configure experiment tracking:

```json
"mlflow": {
  "tracking_uri": "http://localhost:8001",
  "experiment_name": "rag_pipeline",
  "run_name": "default_run"
}
```

## Complete Example

Here's a complete example of the config.json file:

```json
{
  "paths": {
    "index_file": "data/vector_store/index.faiss",
    "metadata_file": "data/vector_store/metadata.pkl",
    "data_file": "data/processed/combined_data.json"
  },
  "llm": {
    "client": "openai",
    "model": "gpt-3.5-turbo",
    "temperature": 0.3,
    "max_tokens": 500
  },
  "embedding": {
    "model": "sentence-transformers/all-MiniLM-L6-v2"
  },
  "retriever_args": {
    "top_k": 5,
    "similarity_threshold": 0.7
  },
  "mlflow": {
    "tracking_uri": "http://localhost:8001",
    "experiment_name": "rag_pipeline",
    "run_name": "default_run"
  }
}
```

## How to Apply Changes

After modifying the `config.json` file:
1. Save the file
2. Restart the RAG service if it's running
3. Changes will be automatically loaded by the `ConfigLoader` class when the application starts

No further steps are required as the configuration is loaded at runtime.