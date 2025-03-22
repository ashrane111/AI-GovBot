import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main.rag_pipeline import RAGPipeline

def main():
    pipeline = RAGPipeline()
    query = input("Enter your query: ")
    pipeline.run(query)

if __name__ == "__main__":
    main()