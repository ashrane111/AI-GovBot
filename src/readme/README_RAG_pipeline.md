# RAG Pipeline

This module implements a Retrieval-Augmented Generation (RAG) pipeline that combines document retrieval with large language model (LLM) generation to produce grounded responses. It is modular, configurable, and supports multiple LLM providers.

## Overview

![Rag Flowchart](Rag_flowchart.drawio.png)

The RAG Pipeline performs the following steps:

1. **Document Retrieval**: Uses FAISS with sentence-transformer embeddings to retrieve top-3 relevant documents from a local index.
2. **Prompt Construction**: Formats the retrieved context and user query into a structured prompt for the LLM.
3. **LLM Completion**: Sends the prompt to an LLM (OpenAI, HuggingFace, or Ollama) and returns a generated response.
4. **Metric Logging**: Logs query metadata and performance metrics (retrieval/generation time, scores, etc.) using MLflow.

## Key Components

### `rag_pipeline.py`

- Entry point to the pipeline logic
- Calls the retriever, prompt generator, LLM, and MLflow tracker
- Filters retrieved documents based on a configurable score threshold

### `retriever.py`

- Loads FAISS vector index using `SentenceTransformerEmbeddings`
- Performs similarity search with scoring

### `generator.py`

- Initializes the LLM client using a factory method
- Sends structured prompts and returns generated completions

### `prompt_gen.py`

- Prepends a system prompt and formats the user query and context
- Ensures consistent communication with the LLM

### `mlflow_tracker.py`

- Logs parameters (e.g., query, document snippets)
- Logs metrics such as retrieval time, generation time, and response length

## LLM Client Abstraction

LLM clients are defined in `llm_clients/`, adhering to a common interface:

- `openai_client.py`
- `hugging_face_client.py`
- `ollama_local_client.py`
- Additional clients can be added via the `client_factory.py`

## Configuration

All runtime parameters are set via `config.json` and loaded using `config_loader.py`.

Key configuration options:

- `retriever_args`: number of documents and similarity threshold
- `embedding.model`: sentence-transformers model
- `llm.client`: LLM backend to use (e.g., `openai`)
- `mlflow`: URI and experiment name
- `paths`: index and data file locations

## How It Works

```text
User Query
   ↓
Retriever (FAISS + Embeddings)
   ↓
Top-k Documents + Scores
   ↓
PromptGen (Context + Query → Prompt)
   ↓
LLM Client (e.g., OpenAI, HF, Ollama)
   ↓
Generated Response
   ↓
MLflow Logs (Query, Docs, Times)
   ↓
Final Answer


*Since this pipeline uses pretrained large language models (LLMs), tasks such as hyperparameter tuning, sensitivity analysis, and pushing models to an artifact registry are not applicable.*  
 



## About Bias Detection
Please refer to [Bias Detection Readme](src/readme/README_bias_detection.md)

