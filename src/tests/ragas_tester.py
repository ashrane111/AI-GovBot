#!/usr/bin/env python3
# filepath: /home/rixirx/Trials and Experiments/MLOps Trials/AI-GovBot/src/tests/run_rag_evaluation.py
import os
import sys
import json
import time
import asyncio
import argparse
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from unittest.mock import patch, MagicMock
from datetime import datetime
import subprocess
import atexit

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import after setting the path
from rag_evaluator import RAGEvaluator
from main.rag_pipeline import RAGPipeline

def start_mlflow():
    global mlflow_process
    mlflow_process = subprocess.Popen(["mlflow", "server", "--host", "0.0.0.0", "--port", "8001"])

def stop_mlflow():
    global mlflow_process
    if mlflow_process:
        mlflow_process.terminate()
        mlflow_process.wait()

def setup_arg_parser():
    """Configure command line arguments"""
    parser = argparse.ArgumentParser(description="Run RAG evaluation tests")
    parser.add_argument("--mode", choices=["real", "mock"], default="mock", 
                        help="Run with real models or mock components")
    parser.add_argument("--output", default="rag_eval_results.json", 
                        help="Output file path for results")
    parser.add_argument("--visualize", action="store_true", 
                        help="Generate visualization of results")
    return parser.parse_args()

def mock_embeddings_model():
    """Create a mock for SentenceTransformerEmbeddings"""
    mock_embeddings = MagicMock()
    mock_embeddings.embed_query.return_value = [0.1] * 384  # Mock embedding vector
    return mock_embeddings

def mock_retriever():
    """Create a mock for Retriever"""
    mock_ret = MagicMock()
    mock_ret.retrieve.return_value = (
        ["Mock document 1", "Mock document 2"],
        [0.2, 0.5]
    )
    return mock_ret

async def run_real_evaluation():
    """Run evaluation with real components"""
    print("=== Starting Real RAG Evaluation ===")
    print("Initializing pipeline...")
    pipeline = RAGPipeline()
    
    print("Initializing evaluator...")
    evaluator = RAGEvaluator(pipeline)
    
    print("Running evaluation...")
    results = await evaluator.evaluate_generation()
    
    print("Generating summary...")
    results_dict = evaluator.summarize_results(results)
    
    return results, results_dict

async def run_mocked_evaluation():
    """Run evaluation with mocked components"""
    print("=== Starting Mocked RAG Evaluation ===")
    
    # Create patcher for SentenceTransformerEmbeddings
    with patch('main.embeddings_model.SentenceTransformerEmbeddings', return_value=mock_embeddings_model()):
        # Create a RAG pipeline with the mocked embeddings
        print("Initializing pipeline with mocks...")
        pipeline = RAGPipeline()
        
        # Optionally replace the retriever with a mock
        pipeline.retriever = mock_retriever()
        
        print("Initializing evaluator...")
        evaluator = RAGEvaluator(pipeline)
        
        print("Running evaluation...")
        results = await evaluator.evaluate_generation()
        
        print("Generating summary...")
        results_dict = evaluator.summarize_results(results)
        
        return results, results_dict

def save_results(results, results_dict, output_path):
    """Save evaluation results to file"""
    # Create a directory for outputs if it doesn't exist
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    
    # Prepare output data
    output_data = {
        "summary": results_dict,
        "detailed_results": [dict(r) for r in results],
        "timestamp": datetime.now().isoformat()
    }
    
    # Save to JSON
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"Results saved to {output_path}")

def visualize_results(results, results_dict, output_dir='.'):
    """Generate visualizations from evaluation results"""
    print("Generating visualizations...")
    
    # Create directory for visualizations
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Bar chart of average metrics
    plt.figure(figsize=(10, 6))
    metrics = ['avg_faithfulness', 'avg_relevance']
    values = [results_dict[m] for m in metrics]
    
    sns.barplot(x=metrics, y=values)
    plt.title("RAG Evaluation Metrics")
    plt.ylabel("Score")
    plt.ylim(0, 1)
    plt.savefig(os.path.join(output_dir, "rag_metrics.png"))
    
    # 2. Detailed metrics for each query
    plt.figure(figsize=(12, 8))
    
    # Convert results to DataFrame
    df = pd.DataFrame([{
        'query': r['query'][:30] + '...' if len(r['query']) > 30 else r['query'],
        'faithfulness': r['faithfulness'],
        'relevance': r['relevance']
    } for r in results])
    
    # Reshape for seaborn
    df_melted = pd.melt(df, id_vars=['query'], var_name='metric', value_name='score')
    
    # Plot
    sns.barplot(x='query', y='score', hue='metric', data=df_melted)
    plt.title("Metrics by Query")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "query_metrics.png"))
    
    print(f"Visualizations saved to {output_dir}")

async def main():
    # Parse arguments
    args = setup_arg_parser()
    
    try:
        # Run evaluation based on mode
        if args.mode == "real":
            results, results_dict = await run_real_evaluation()
        else:
            results, results_dict = await run_mocked_evaluation()
        
        # Save results
        save_results(results, results_dict, args.output)
        
        # Visualize if requested
        if args.visualize:
            visualize_results(results, results_dict, os.path.dirname(args.output))
        
        print("\n=== Evaluation Complete ===")
        print(f"Average Faithfulness: {results_dict['avg_faithfulness']:.2f}")
        print(f"Average Relevance: {results_dict['avg_relevance']:.2f}")
        
        return results_dict
        
    except Exception as e:
        print(f"Error during evaluation: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # Ensure event loop is properly set up
    start_mlflow()
    atexit.register(stop_mlflow)
    try:
        import nest_asyncio
        nest_asyncio.apply()
    except ImportError:
        print("Warning: nest_asyncio not available, may cause issues with asyncio in notebooks/IDEs")
    
    # Run the evaluation
    result = asyncio.run(main())