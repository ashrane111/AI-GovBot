# AI-GovBot: HARVEY

<p align="center">
  <img src="assets/images/logo_simple.png" alt="HARVEY - AI FOR LAWS" width="300"/>
</p>

A chatbot powered by Retrieval-Augmented Generation (RAG) that leverages the AI Governance and Regulatory Archive (AGORA) dataset to help organizations navigate AI-related laws and regulations.

## Overview

HARVEY is an intelligent legal assistant that provides accurate information and insights about AI regulations, policies, and compliance requirements. By combining advanced retrieval mechanisms with generative AI, HARVEY delivers contextually relevant responses to legal queries related to artificial intelligence governance.

## Accessing Project Components

- [Data Pipeline Documentation](data/data-pipeline/README.md)
- [RAG Pipeline Documentation](src/readme/README_RAG_pipeline.md)
- [Web Application Documentation](src/readme/README_web_app.md)

## Features

- **Regulatory Search**: Query AI-related laws and policies from the AGORA dataset
- **Intelligent Summarization**: Retrieve and summarize legal texts with actionable insights
- **Context-Aware Responses**: Get answers that consider the broader legal context
- **User-Friendly Interface**: Intuitive chatbot interface for seamless interaction
- **High-Quality Knowledge**: Fine-tuned language models for contextually relevant responses
- **Citation Support**: Responses include sources and relevant legal citations

## Deployment

HARVEY can be deployed using our automated deployment scripts:

### Model Deployment (GKE)

Deploy the HARVEY application on Google Kubernetes Engine:
- [Model Deployment Instructions](deployment_scripts/model-deployment/model-deploy_readme.md)
- Run `./deployment_scripts/model-deployment/model-deploy.sh` to deploy
- For rollbacks: `./deployment_scripts/model-deployment/rollback.sh`

### Data Pipeline Deployment (Airflow on VM)

Deploy the data processing pipeline on a GCP VM with Airflow:
- [Data Pipeline Deployment Instructions](deployment_scripts/data-pipeline-deployment/data-pipeline-deploy_readme.md)
- Run `./deployment_scripts/data-pipeline-deployment/pr_setup_airflow_vm.sh` to set up the VM

### Deployment Prerequisites

- Google Cloud Platform account with billing enabled
- gcloud CLI installed and configured
- Docker installed for local development and testing
- Kubernetes (kubectl) for interacting with GKE
- API keys for OpenAI/other LLM providers

## Tech Stack

- **Python**: For preprocessing, model integration, and chatbot development
- **Vector Databases**:
  - FAISS: For efficient vector-based document retrieval
  - Weaviate: For semantic search capabilities
- **NLP & ML**:
  - Hugging Face Transformers: For fine-tuning and deploying NLP models
  - LangChain: For building RAG pipelines
- **User Interface**:
  - Streamlit: For building an intuitive web interface
  - Gradio: For interactive demo components
- **Deployment**:
  - Google Kubernetes Engine (GKE): For application hosting
  - Artifact Registry: For Docker image management
  - Compute Engine VMs: For Airflow orchestration
  - Docker: For containerization

## How to Use

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/AI-GovBot.git
   cd AI-GovBot
   ```

2. Set up dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Configure the AGORA dataset following the [data pipeline documentation](data/data-pipeline/README.md)

4. Launch the application:
   ```
   cd src
   streamlit run app.py
   ```

5. Input your legal queries and receive insights instantly!

For production deployment, follow the [deployment instructions](#deployment) above.

